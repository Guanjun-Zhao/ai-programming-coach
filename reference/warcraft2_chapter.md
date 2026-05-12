# 第 2 章　继承与多态：让每种武士各具特点

在上一章中，五种武士的降生消息格式完全相同，我们只用一个 `Warrior` 类就处理完了全部逻辑。这一章的题目在此基础上增加了新需求：dragon 有士气和武器，ninja 有两件武器，iceman 有一件武器，lion 有忠诚度，wolf 什么都没有——五种武士的**属性和打印格式各不相同**。

如果仍然用一个类来描述所有武士，类里就需要堆满"如果是 dragon 就…否则如果是 ninja 就…"的判断，代码会越来越臃肿。C++ 为这种场景提供了一个更优雅的方案：**继承**。我们把所有武士共有的属性和行为放在基类 `CWarrior` 里，再为每种武士单独派生一个子类，让每个子类自己负责自己独特的属性和打印逻辑。

在本章中，你还将学到**虚函数**和**多态**——它们让司令部的 `Produce()` 方法可以统一调用 `PrintResult()`，而无需关心当前这名武士究竟是哪种类型。

> **注意：** 本章的代码在上一章的基础上修改。类名前缀从 `Warrior`/`Headquarter` 改为 `CWarrior`/`CHeadquarter`（C 代表 Class），这是很多 C++ 项目的命名惯例，有助于在代码中快速区分类名和变量名。

## 2.1　规划新功能

与上一章相比，这次的改动集中在三处：

第一，新增一个 `CWeapon` 类，用来描述武器的种类和攻击力。第二，把原来的 `Warrior` 类改造为**抽象基类** `CWarrior`，把公共的属性和降生消息的公共部分留在里面，再派生出 `CDragon`、`CNinja`、`CIceman`、`CLion`、`CWolf` 五个子类，每个子类各自处理自己独特的属性。第三，`CHeadquarter::Produce()` 里用 `switch` 语句，根据武士种类创建对应的子类对象。`CHeadquarter` 的整体结构基本不变，主函数几乎一字未动。

## 2.2　新增武器类

下面来创建 `CWeapon` 类，把三种武器的名称和攻击力统一管理。

在宏定义 `WEAPON_NUM = 3` 之后声明 `CWeapon` 类。类的公开成员包括：整型 `nKindNo`（武器种类编号，0=sword，1=bomb，2=arrow）和整型 `nForce`（攻击力），这两个字段全部公开，各武士子类在构造时可以直接为自己的武器赋值。此外还有两个静态成员：整型数组 `InitialForce` 存放三种武器的初始攻击力，字符串指针数组 `Names` 存放三种武器的名称——静态成员在内存里只有一份，所有武器实例共享。

## 2.3　改造 CWarrior 基类

### 2.3.1　声明与虚函数

下面来重新声明 `CWarrior` 类。首先用 `enum` 定义五个具名常量 `DRAGON`、`NINJA`、`ICEMAN`、`LION`、`WOLF`，它们的值依次为 0、1、2、3、4，与 `InitialLifeValue` 数组的下标一一对应。写 `DRAGON` 比写 `0` 可读性好得多，也不容易出错。

在前向声明 `class CHeadquarter;` 之后声明 `CWarrior` 类。与上一章相比有以下几处关键变化：

成员访问控制从 `private` 改成了 `protected`。`private` 成员只有本类能访问，子类也访问不到；改成 `protected` 后，`pHeadquarter` 和 `nNo` 这两个成员在子类中同样可以直接读取——各武士子类在构造时都需要用到它们。

公开部分包含两个 `PrintResult` 重载。第一个带两个参数（时间和武士种类），加了 `virtual` 关键字，负责打印所有武士共同的降生消息格式，可以被子类重写。第二个只带时间参数，声明为 `virtual void PrintResult(int nTime) = 0`，是**纯虚函数**：`= 0` 意味着基类不提供实现，强制要求每个子类必须自己实现；含有纯虚函数的类叫**抽象类**，不能直接创建对象，这完全符合我们的设计意图。

最后，析构函数声明为 `virtual ~CWarrior() {}`。这一行非常重要：`Produce()` 里存储的是 `CWarrior*` 类型的指针，析构时调用 `delete pWarriors[i]`；如果析构函数不是虚的，`delete` 只会调用基类析构函数而跳过子类析构函数，导致子类的成员没有被正确释放。

> **注意：** "只要基类中有虚函数，析构函数就应该声明为虚的"——这条规则记住了，以后用多态时就不会踩坑。

### 2.3.2　基类的 PrintResult

`CWarrior` 的构造函数接受司令部指针 `p` 和武士编号 `nNo_`，直接赋给对应的 `protected` 成员。

带两个参数的 `PrintResult(int nTime, int nKindNo)` 是所有子类共用的公共打印逻辑。它先调用 `pHeadquarter->GetColor(szColor)` 把颜色写入一个字符数组——注意这里 `GetColor()` 的签名与上一章不同，改成了接受 `char*` 参数并将结果写入其中，而不是返回 `string`。随后用 `printf` 按格式打印完整的降生消息，参数依次是时间、颜色、武士名称、编号、初始生命值、该类武士的已降生数量，以及结尾的 `in X headquarter`。每个子类的 `PrintResult(int nTime)` 都会先调用这个基类版本打印公共部分，再自己追加特有信息。

## 2.4　为每种武士创建子类

### 2.4.1　CDragon：士气与武器

`CDragon` 继承自 `CWarrior`，使用 `: public CWarrior` 语法声明。`public` 继承意味着基类的 `public` 和 `protected` 成员在子类中保持相同的访问权限。

私有成员包含一个 `CWeapon` 对象 `wp` 和一个 `double` 类型的士气值 `fmorale`。

构造函数使用**初始化列表**语法 `: CWarrior(p, nNo_)` 调用基类构造函数——这是 C++ 中子类构造函数向父类传参的标准写法，必须写在初始化列表里，不能在函数体内调用。函数体内，武器种类由 `nNo % WEAPON_NUM` 决定（编号 1 的 dragon 拿 sword，编号 2 的拿 bomb，编号 3 的拿 arrow，如此循环），并从 `CWeapon::InitialForce` 表中读取对应攻击力。士气值等于司令部在生产完这名 dragon **之后**的剩余生命元除以 dragon 的初始生命值，用浮点数存储；注意除法时必须强制转换为 `double`，否则整数除法会丢失小数部分。

`PrintResult(int nTime)` 先调用 `CWarrior::PrintResult(nTime, DRAGON)` 打印公共的降生消息，再打印 dragon 特有的武器和士气信息。这种"先调用基类版本，再追加子类内容"的写法是 C++ 重写虚函数时的常见模式。

### 2.4.2　CNinja：双持武器

`CNinja` 继承自 `CWarrior`，私有成员是一个长度为 2 的 `CWeapon` 数组 `wps`，结构上和 `CDragon` 只差一件武器。构造函数在初始化列表调用基类构造函数后，在函数体内为两件武器分别赋值：第一件的种类编号为 `nNo % 3`，第二件为 `(nNo + 1) % 3`，保证编号相邻但取模后不同。`PrintResult` 打印公共部分后，再输出两件武器的名称。

### 2.4.3　CIceman、CLion 与 CWolf

`CIceman` 与 `CDragon` 结构几乎相同，只有一件武器，没有士气字段，`PrintResult` 打印公共部分后只追加一行武器名称。

`CLion` 没有武器，但有一个 `int nLoyalty`（忠诚度）私有字段。构造函数和 `PrintResult` 都通过 `pHeadquarter->GetTotalLifeValue()` 读取司令部当前的剩余生命元来赋值或打印——题目要求打印的是降生**后**的剩余生命元，而构造函数在 `Produce()` 扣减生命元之后才被调用，所以两处读到的值相同，都是正确的结果。

`CWolf` 最简单，没有任何额外属性，构造函数只调用基类构造函数，`PrintResult` 只调用基类版本，不追加任何内容。

## 2.5　改造 Produce()：用 switch 创建子类对象

`Produce()` 的整体逻辑和上一章完全相同——跳过造不起的武士、扣减生命元、打印停产消息。唯一的变化是创建武士对象的那一步，从一行 `new Warrior(...)` 变成了一段 `switch`：根据 `nKindNo` 分五个分支，分别用 `new` 创建对应子类的对象，把指针存入 `pWarriors` 数组。数组的类型是 `CWarrior*`——同一个指针类型指向任何一种子类对象，这正是**多态**的体现。

创建完毕后，统一调用 `pWarriors[nTotalWarriorNum]->PrintResult(nTime)`。因为 `PrintResult(int nTime)` 是虚函数，C++ 会在运行时根据指针实际指向的对象类型，自动调用正确的子类版本。`Produce()` 完全不需要知道当前武士是什么类型，这就是多态带来的简洁。

## 2.6　GetColor() 和静态成员

`GetColor()` 的签名从上一章的"返回 `string`"改为接受 `char*` 参数并用 `strcpy` 写入：若 `nColor` 为 0 则写入 `"red"`，否则写入 `"blue"`。这样做是为了避免在 `printf` 的格式串中混用 `string` 和 `const char*`。

文件末尾定义所有静态成员。`CWeapon::Names` 初始化为 `{"sword", "bomb", "arrow"}`，`CWeapon::InitialForce` 只申请内存，本题暂时不读入（为后续扩展预留）。`CWarrior::Names` 和 `CWarrior::InitialLifeValue` 与上一章相同。`CHeadquarter::MakingSeq` 的初始化数据不变，仍是 `{2,3,4,1,0}` 和 `{3,0,1,2,4}`。与上一章相比，这里多了 `CWeapon` 的两个静态成员定义。

## 2.7　主函数几乎不变

主函数的结构和上一章完全一样，改动只有类名前缀从 `Warrior`/`Headquarter` 改为 `CWarrior`/`CHeadquarter`。读入组数后，对每组数据打印 `Case:n`，读入生命元和五种武士的初始生命值，用 `Init()` 重置红蓝司令部，内层循环每轮先红后蓝各调用一次 `Produce()`，分别用 `tmp1`、`tmp2` 接收返回值，双方均返回 0 时退出。

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
