# 第 2 章　继承与多态：让每种武士各具特点

在上一章中，五种武士的降生消息格式完全相同，我们只用一个 `Warrior` 类就处理完了全部逻辑。这一章的题目在此基础上增加了新需求：dragon 有士气和武器，ninja 有两件武器，iceman 有一件武器，lion 有忠诚度，wolf 什么都没有——五种武士的**属性和打印格式各不相同**。

如果仍然用一个类来描述所有武士，类里就需要堆满"如果是 dragon 就…否则如果是 ninja 就…"的判断，代码会越来越臃肿。C++ 为这种场景提供了一个更优雅的方案：**继承**。我们把所有武士共有的属性和行为放在基类 `CWarrior` 里，再为每种武士单独派生一个子类，让每个子类自己负责自己独特的属性和打印逻辑。

在本章中，你还将学到**虚函数**和**多态**——它们让司令部的 `Produce()` 方法可以统一调用 `PrintResult()`，而无需关心当前这名武士究竟是哪种类型。

> **注意：** 本章的代码在上一章的基础上修改。类名前缀从 `Warrior`/`Headquarter` 改为 `CWarrior`/`CHeadquarter`（C 代表 Class），这是很多 C++ 项目的命名惯例，有助于在代码中快速区分类名和变量名。

## 2.1　规划新功能

与上一章相比，这次的改动集中在三处：

第一，新增一个 `CWeapon` 类，用来描述武器的种类和攻击力。第二，把原来的 `Warrior` 类改造为**抽象基类** `CWarrior`，把公共的属性和降生消息的公共部分留在里面，再派生出 `CDragon`、`CNinja`、`CIceman`、`CLion`、`CWolf` 五个子类，每个子类各自处理自己独特的属性。第三，`CHeadquarter::Produce()` 里用 `switch` 语句，根据武士种类创建对应的子类对象。`CHeadquarter` 的整体结构基本不变，主函数几乎一字未动。

## 2.2　新增武器类

下面来创建 `CWeapon` 类，把三种武器的名称和攻击力统一管理：

```cpp
// warcraft2.cpp
--snip--
#define WEAPON_NUM 3

class CWeapon
{
    public:
        int nKindNo;                          // ①
        int nForce;
        static int InitialForce[WEAPON_NUM];  // ②
        static const char* Names[WEAPON_NUM]; // ②
};
```

在①处，每件武器用两个整数描述：`nKindNo` 是种类编号（0=sword，1=bomb，2=arrow），`nForce` 是攻击力。`CWeapon` 的数据全部公开，这样各种武士子类在构造时可以直接为自己的武器赋值。

在②处，名字表和攻击力表是静态成员，整个程序只存一份，所有武器实例共享。

## 2.3　改造 CWarrior 基类

### 2.3.1　声明与虚函数

下面来重新声明 `CWarrior` 类。这次它是一个**基类**，和上一章相比有几处关键变化：

```cpp
// warcraft2.cpp
--snip--
enum { DRAGON, NINJA, ICEMAN, LION, WOLF };   // ①

class CHeadquarter;
class CWarrior
{
    protected:                                 // ②
        CHeadquarter* pHeadquarter;
        int nNo;
    public:
        static const char* Names[WARRIOR_NUM];
        static int InitialLifeValue[WARRIOR_NUM];
        CWarrior(CHeadquarter* p, int nNo_);
        virtual void PrintResult(int nTime, int nKindNo);  // ③
        virtual void PrintResult(int nTime) = 0;           // ④
        virtual ~CWarrior() { }                            // ⑤
};
```

在①处，用 `enum` 定义了五个具名常量 `DRAGON`、`NINJA`……它们的值依次为 0、1、2、3、4，和 `InitialLifeValue` 数组的下标对应。写 `DRAGON` 比写 `0` 可读性好得多，也不容易出错。

在②处，成员访问控制从上一章的 `private` 改成了 `protected`。`private` 成员只有本类能访问，子类也访问不到；改成 `protected` 后，子类就能直接读取 `pHeadquarter` 和 `nNo` 了——各武士子类在构造时都需要用到这两个成员。

在③处，`virtual void PrintResult(int nTime, int nKindNo)` 是带种类参数的版本，负责打印**所有武士共同的**降生消息格式。`virtual` 关键字说明这个函数可以被子类重写。

在④处，`virtual void PrintResult(int nTime) = 0` 是**纯虚函数**。`= 0` 意味着基类不提供实现，强制要求每个子类必须自己实现这个函数。含有纯虚函数的类叫**抽象类**，不能直接创建对象——这完全符合我们的设计：程序里只会创建 `CDragon`、`CNinja` 等具体子类的对象，不会创建"泛泛的武士"。

在⑤处，`virtual ~CWarrior() {}` 是**虚析构函数**。这一行非常重要：`Produce()` 里存储的是 `CWarrior*` 类型的指针，析构时调用 `delete pWarriors[i]`；如果析构函数不是虚的，`delete` 只会调用基类析构函数而跳过子类析构函数，导致子类的成员没有被正确释放。

> **注意：** "只要基类中有虚函数，析构函数就应该声明为虚的"——这条规则记住了，以后用多态时就不会踩坑。

### 2.3.2　基类的 PrintResult

下面来实现 `CWarrior` 的公共打印函数：

```cpp
// warcraft2.cpp
--snip--
CWarrior::CWarrior(CHeadquarter* p, int nNo_)
{
    nNo          = nNo_;
    pHeadquarter = p;
}

void CWarrior::PrintResult(int nTime, int nKindNo)
{
    char szColor[20];
    pHeadquarter->GetColor(szColor);   // ①
    printf("%03d %s %s %d born with strength %d,%d %s in %s headquarter\n",
           nTime, szColor, Names[nKindNo], nNo, InitialLifeValue[nKindNo],
           pHeadquarter->anWarriorNum[nKindNo], Names[nKindNo], szColor);
}
```

在①处，`GetColor()` 的签名和上一章不同：这次它接受一个 `char*` 参数，把结果写进去，而不是返回 `string`。每个子类的 `PrintResult(int nTime)` 会先调用这个基类版本打印公共部分，再自己打印额外信息。

## 2.4　为每种武士创建子类

### 2.4.1　CDragon：士气与武器

```cpp
// warcraft2.cpp
--snip--
class CDragon : public CWarrior   // ①
{
    private:
        CWeapon wp;
        double fmorale;
    public:
        CDragon(CHeadquarter* p, int nNo_) : CWarrior(p, nNo_)   // ②
        {
            wp.nKindNo = nNo % WEAPON_NUM;                        // ③
            wp.nForce  = CWeapon::InitialForce[wp.nKindNo];
            fmorale    = pHeadquarter->GetTotalLifeValue()
                         / (double)CWarrior::InitialLifeValue[DRAGON];   // ④
        }
        void PrintResult(int nTime)
        {
            CWarrior::PrintResult(nTime, DRAGON);   // ⑤
            printf("It has a %s,and it's morale is %.2f\n",
                   CWeapon::Names[wp.nKindNo], fmorale);
        }
};
```

在①处，`: public CWarrior` 声明 `CDragon` 继承自 `CWarrior`。`public` 继承意味着基类的 `public` 和 `protected` 成员在子类中保持相同的访问权限。

在②处，构造函数用**初始化列表**的语法 `: CWarrior(p, nNo_)` 调用基类构造函数，把 `p` 和 `nNo_` 交给基类处理。这是 C++ 中子类构造函数传参给父类的标准写法，必须写在初始化列表里，不能在函数体内调用。

在③处，武器的种类由 `nNo % WEAPON_NUM` 决定——编号为 1 的 dragon 拿 sword（0），编号为 2 的拿 bomb（1），编号为 3 的拿 arrow（2），如此循环。

在④处，士气值等于司令部**生产完这名 dragon 之后**的剩余生命元，除以 dragon 的初始生命值，用浮点数存储。注意必须强制转换为 `double` 再做除法，否则整除会丢失小数部分。

在⑤处，先调用 `CWarrior::PrintResult(nTime, DRAGON)` 打印公共的降生消息，再打印 dragon 特有的武器和士气信息。这种"先调用基类版本，再追加子类内容"的写法是 C++ 重写虚函数时的常见模式。

### 2.4.2　CNinja：双持武器

```cpp
// warcraft2.cpp
--snip--
class CNinja : public CWarrior
{
    private:
        CWeapon wps[2];   // ①
    public:
        CNinja(CHeadquarter* p, int nNo_) : CWarrior(p, nNo_)
        {
            wps[0].nKindNo = nNo % WEAPON_NUM;          // ②
            wps[0].nForce  = CWeapon::InitialForce[wps[0].nKindNo];
            wps[1].nKindNo = (nNo + 1) % WEAPON_NUM;   // ②
            wps[1].nForce  = CWeapon::InitialForce[wps[1].nKindNo];
        }
        void PrintResult(int nTime)
        {
            CWarrior::PrintResult(nTime, NINJA);
            printf("It has a %s and a %s\n",
                   CWeapon::Names[wps[0].nKindNo],
                   CWeapon::Names[wps[1].nKindNo]);
        }
};
```

在①处，ninja 持有一个长度为 2 的武器数组，结构上和 dragon 只差一件武器。

在②处，两件武器的编号分别是 `nNo % 3` 和 `(nNo + 1) % 3`，保证编号相邻但取模后不同。

### 2.4.3　CIceman、CLion 与 CWolf

iceman 和 dragon 的结构几乎相同，只有一件武器，没有士气：

```cpp
// warcraft2.cpp
--snip--
class CIceman : public CWarrior
{
    private:
        CWeapon wp;
    public:
        CIceman(CHeadquarter* p, int nNo_) : CWarrior(p, nNo_)
        {
            wp.nKindNo = nNo % WEAPON_NUM;
            wp.nForce  = CWeapon::InitialForce[wp.nKindNo];
        }
        void PrintResult(int nTime)
        {
            CWarrior::PrintResult(nTime, ICEMAN);
            printf("It has a %s\n", CWeapon::Names[wp.nKindNo]);
        }
};
```

lion 没有武器，但有忠诚度属性，其值等于生产完 lion 之后司令部的剩余生命元：

```cpp
// warcraft2.cpp
--snip--
class CLion : public CWarrior
{
    private:
        int nLoyalty;
    public:
        CLion(CHeadquarter* p, int nNo_) : CWarrior(p, nNo_)
        {
            nLoyalty = pHeadquarter->GetTotalLifeValue();   // ①
        }
        void PrintResult(int nTime)
        {
            CWarrior::PrintResult(nTime, LION);
            nLoyalty = pHeadquarter->GetTotalLifeValue();   // ①
            printf("It's loyalty is %d\n", nLoyalty);
        }
};
```

在①处，忠诚度在构造时和打印时各算一次。题目要求打印的是降生**后**的剩余生命元，而构造函数在 `Produce()` 扣减生命元之后才被调用，所以两处都读同一个值。

wolf 最简单，没有任何额外属性：

```cpp
// warcraft2.cpp
--snip--
class CWolf : public CWarrior
{
    public:
        CWolf(CHeadquarter* p, int nNo_) : CWarrior(p, nNo_) { }
        void PrintResult(int nTime)
        {
            CWarrior::PrintResult(nTime, WOLF);
        }
};
```

## 2.5　改造 Produce()：用 switch 创建子类对象

`Produce()` 的整体逻辑和上一章完全相同——跳过造不起的武士、扣减生命元、打印停产消息。唯一的变化是创建武士对象的那一步，从一行 `new Warrior(...)` 变成了一段 `switch`：

```cpp
// warcraft2.cpp
--snip--
int CHeadquarter::Produce(int nTime)
{
    --snip--
    nTotalLifeValue -= CWarrior::InitialLifeValue[nKindNo];
    nCurMakingSeqIdx = (nCurMakingSeqIdx + 1) % WARRIOR_NUM;
    anWarriorNum[nKindNo]++;
    switch (nKindNo)                                                // ①
    {
        case DRAGON:
            pWarriors[nTotalWarriorNum] = new CDragon(this, nTotalWarriorNum+1);
            break;
        case NINJA:
            pWarriors[nTotalWarriorNum] = new CNinja(this, nTotalWarriorNum+1);
            break;
        case ICEMAN:
            pWarriors[nTotalWarriorNum] = new CIceman(this, nTotalWarriorNum+1);
            break;
        case LION:
            pWarriors[nTotalWarriorNum] = new CLion(this, nTotalWarriorNum+1);
            break;
        case WOLF:
            pWarriors[nTotalWarriorNum] = new CWolf(this, nTotalWarriorNum+1);
            break;
    }
    pWarriors[nTotalWarriorNum]->PrintResult(nTime);               // ②
    nTotalWarriorNum++;
    return 1;
}
```

在①处，`switch` 根据 `nKindNo` 创建对应的子类对象，把指针存进 `pWarriors` 数组。数组的类型是 `CWarrior*`——这正是**多态**的体现：同一个指针类型可以指向任何一种子类对象。

在②处，调用 `pWarriors[nTotalWarriorNum]->PrintResult(nTime)`。因为 `PrintResult(int nTime)` 是虚函数，C++ 会在运行时根据指针实际指向的对象类型，自动调用正确的子类版本——`CDragon` 的就调用 `CDragon::PrintResult`，`CLion` 的就调用 `CLion::PrintResult`。`Produce()` 完全不需要知道当前武士是什么类型，这就是多态带来的简洁。

## 2.6　GetColor() 和静态成员

`GetColor()` 的实现改为写入外部字符数组：

```cpp
// warcraft2.cpp
--snip--
void CHeadquarter::GetColor(char* szColor)
{
    if (nColor == 0) strcpy(szColor, "red");
    else             strcpy(szColor, "blue");
}
```

静态成员的定义在文件末尾：

```cpp
// warcraft2.cpp
--snip--
const char* CWeapon::Names[WEAPON_NUM]     = {"sword", "bomb", "arrow"};
int         CWeapon::InitialForce[WEAPON_NUM];

const char* CWarrior::Names[WARRIOR_NUM]   = {"dragon","ninja","iceman","lion","wolf"};
int         CWarrior::InitialLifeValue[WARRIOR_NUM];
int         CHeadquarter::MakingSeq[2][WARRIOR_NUM] = { {2,3,4,1,0}, {3,0,1,2,4} };
```

与上一章相比，这里多了 `CWeapon` 的两个静态成员定义。`InitialForce` 本题暂时不读入，是为后续扩展预留的接口。

## 2.7　主函数几乎不变

主函数的结构和上一章完全一样，改动只有类名前缀：

```cpp
// warcraft2.cpp
--snip--
int main()
{
    int t, m;
    CHeadquarter RedHead, BlueHead;
    scanf("%d", &t);
    int nCaseNo = 1;
    while (t--)
    {
        printf("Case:%d\n", nCaseNo++);
        scanf("%d", &m);
        for (int i = 0; i < WARRIOR_NUM; i++)
            scanf("%d", &CWarrior::InitialLifeValue[i]);
        RedHead.Init(0, m);
        BlueHead.Init(1, m);
        int nTime = 0;
        while (true)
        {
            int tmp1 = RedHead.Produce(nTime);
            int tmp2 = BlueHead.Produce(nTime);
            if (tmp1 == 0 && tmp2 == 0)
                break;
            nTime++;
        }
    }
    return 0;
}
```

这正是继承和多态带来的好处：新增了五种子类、新增了武器系统，主函数却完全不需要修改。所有扩展都被封装在各自的类里，对外暴露的接口（`Produce()`、`PrintResult()`）保持不变。

如果此时编译并运行程序，输入样例：

```
1
20
3 4 5 6 7
```

你应该看到如下输出：

```
Case:1
000 red iceman 1 born with strength 5,1 iceman in red headquarter
It has a bomb
000 blue lion 1 born with strength 6,1 lion in blue headquarter
It's loyalty is 14
001 red lion 2 born with strength 6,1 lion in red headquarter
It's loyalty is 9
001 blue dragon 2 born with strength 3,1 dragon in blue headquarter
It has a arrow,and it's morale is 3.67
002 red wolf 3 born with strength 7,1 wolf in red headquarter
002 blue ninja 3 born with strength 4,1 ninja in blue headquarter
It has a sword and a bomb
003 red headquarter stops making warriors
003 blue iceman 4 born with strength 5,1 iceman in blue headquarter
It has a bomb
004 blue headquarter stops making warriors
```
