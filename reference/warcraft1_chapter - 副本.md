# 第 X 章　用类建模：魔兽世界备战

在本章中，我们将解决一道经典的面向对象建模题——魔兽世界备战。题目要求模拟两个司令部按固定顺序循环生产武士，直到生命元耗尽为止，并按时间顺序打印每一个事件。

这道题最值得学习的地方不是算法，而是**如何用类把现实场景翻译成代码**。两个司令部的行为几乎完全对称，如果用全局变量各写一套，代码会立刻变成一团乱麻。用类封装之后，红方和蓝方只是同一套逻辑的两个实例，主函数会变得出奇地简洁。

在本章中，你将定义两个核心类——`Warrior`（武士）和 `Headquarter`（司令部），实现完整的生产逻辑，并学会在 C++ 中使用**静态成员**、**友元类**和**前向声明**这三个常用技巧。

---

## X.1　规划程序

在动手写代码之前，先理清程序需要做哪些事：

1. 读入每组测试数据：初始生命元 M，以及五种武士各自的生命值；
2. 从第 0 小时开始，每小时让**红方先、蓝方后**各尝试生产一名武士；
3. 如果某方当轮造不起按顺序应造的武士，就跳到下一种；五种都造不起则宣告停产；
4. 双方都停产后，本组测试结束。

据此，我们可以设计出程序的骨架：两个 `Headquarter` 对象，一个 `while` 时间循环，循环里轮流调用各自的 `Produce()` 方法。`Warrior` 对象由司令部在 `Produce()` 内部动态创建，负责记录自身属性并打印降生信息。

---

## X.2　定义武士类

### X.2.1　类的声明与静态成员

先把整个文件的开头写出来：

```cpp
// warcraft1.cpp
#include <iostream>
#include <cstdio>
#include <string>
using namespace std;

const int WARRIOR_NUM = 5;

class Headquarter;   // ①

class Warrior
{
    private:
        Headquarter* pHeadquarter;   // ②
        int kindNo;
        int no;
    public:
        static string names[WARRIOR_NUM];            // ③
        static int   initialLifeValue[WARRIOR_NUM];  // ③
        Warrior(Headquarter* p, int no_, int kindNo_);
        void PrintResult(int nTime);
};
```

在 ① 处，写下 `class Headquarter;`，这叫**前向声明**。`Warrior` 类内部需要保存一个指向 `Headquarter` 的指针（见②），但此时 `Headquarter` 的完整定义还没出现。只要我们只用指针、不直接访问成员，编译器见到前向声明就够了——它只需要知道这是一个类的名字。

在 ② 处，`pHeadquarter` 是武士与司令部之间唯一的"通道"。武士打印降生信息时，需要通过它查询司令部的颜色和某类武士的现有数量，这些都是司令部的私有数据。

③ 处的两个 `static` 成员是全班共享的"公告板"。无论创建了多少个 `Warrior` 对象，名字表 `names` 和生命值表 `initialLifeValue` 在内存里只有一份，所有武士都从这里读取自己的属性。

> **注意：** 静态成员变量在类内**声明**，必须在类外**定义**。你会在 X.5 节看到它们真正被赋值的地方。在那之前，它们只是一个"占位承诺"。

### X.2.2　构造函数

下面来实现 `Warrior` 的构造函数，它在司令部每次调用 `new Warrior(...)` 时被执行：

```cpp
// warcraft1.cpp
Warrior::Warrior(Headquarter* p, int no_, int kindNo_)
{
    no           = no_;      // ①
    kindNo       = kindNo_;
    pHeadquarter = p;        // ②
}
```

构造函数只做一件事：把三个传入参数保存下来。① 处，`no_` 和 `kindNo_` 的参数名比成员名多一个下划线——这是 C++ 中常见的命名惯例，专门用来避免写出 `no = no` 这样让人困惑的赋值语句。② 处存入司令部地址，武士从此刻起就"认识"自己的主人了。

### X.2.3　输出降生信息

每当一名武士诞生，就要立刻打印一条降生消息。我们把这个逻辑封装进 `PrintResult()`：

```cpp
// warcraft1.cpp
void Warrior::PrintResult(int nTime)
{
    string color = pHeadquarter->GetColor();  // ①
    printf("%03d %s %s %d born with strength %d,%d %s in %s headquarter\n",
           nTime,
           color.c_str(),                          // ②
           names[kindNo].c_str(),
           no,
           initialLifeValue[kindNo],
           pHeadquarter->warriorNum[kindNo],        // ③
           names[kindNo].c_str(),
           color.c_str());
}
```

① 处调用 `GetColor()` 把颜色整数转成字符串 `"red"` 或 `"blue"`，这个方法我们稍后在 `Headquarter` 中实现。

② 处的 `c_str()` 把 C++ 的 `string` 转成 C 风格的字符指针，因为 `printf` 不直接认识 `string` 类型。

③ 处直接读取了 `Headquarter` 的**私有**成员 `warriorNum[kindNo]`——这能成立，是因为我们在 `Headquarter` 中声明了 `friend class Warrior`，稍后你会看到这行代码。

> **注意：** `%03d` 是 `printf` 的格式说明符，表示"至少输出 3 位整数，不足的在左边补 0"。数字 5 会输出为 `005`，数字 23 会输出为 `023`。这正是题目要求的时间格式。

---

## X.3　定义司令部类

### X.3.1　类的声明

下面来定义 `Headquarter` 类，它是本题逻辑的核心容器：

```cpp
// warcraft1.cpp
class Headquarter
{
    private:
        int  totalLifeValue;              // ①
        bool stopped;                     // ②
        int  totalWarriorNum;
        int  color;                       // ③
        int  curMakingSeqIdx;             // ④
        int  warriorNum[WARRIOR_NUM];     // ⑤
        Warrior* pWarriors[1000];
    public:
        friend class Warrior;             // ⑥
        static int makingSeq[2][WARRIOR_NUM];  // ⑦
        void   Init(int color_, int lv);
        ~Headquarter();
        int    Produce(int nTime);
        string GetColor();
};
```

① `totalLifeValue` 是剩余生命元，每生产一名武士就减少对应数量。

② `stopped` 是一个开关：一旦置为 `true`，司令部就永远停产，以后每次调用 `Produce()` 都直接跳过。

③ `color` 用 0 代表红方、1 代表蓝方。用整数而非字符串，是为了方便在 ⑦ 的二维数组里当下标用。

④ `curMakingSeqIdx` 是生产顺序索引，指向"下一个该轮到谁"，取值在 0 到 4 之间循环。

⑤ `warriorNum` 记录各类武士已生产的数量，武士调用 `PrintResult()` 时需要读取这里。

⑥ `friend class Warrior` 让 `Warrior` 成为 `Headquarter` 的友元，从而允许 `PrintResult()` 直接读取上面的 ⑤。

⑦ `makingSeq` 是一个 2×5 的静态二维数组，存储两个阵营的生产顺序——第一维是阵营（0=红，1=蓝），第二维是先后位置，每个元素是武士的 `kindNo`。

### X.3.2　初始化方法

题目有多组测试数据，同一对司令部对象需要反复使用。我们用 `Init()` 而不是构造函数来重置状态：

```cpp
// warcraft1.cpp
void Headquarter::Init(int color_, int lv)
{
    color           = color_;
    totalLifeValue  = lv;
    totalWarriorNum = 0;
    stopped         = false;           // ①
    curMakingSeqIdx = 0;
    for (int i = 0; i < WARRIOR_NUM; i++)
        warriorNum[i] = 0;             // ②
}
```

① 每组数据开始时，司令部从"未停产"状态出发。② 各类武士的计数也清零，否则上一组数据的数字会串到下一组里去。

> **注意：** 这里选择用 `Init()` 方法而不是构造函数，原因很简单：C++ 的构造函数只在对象刚被创建时调用一次，而 `Init()` 可以在每组数据开始时反复调用。这是竞赛编程中处理多组测试数据的常见做法。

### X.3.3　析构函数：释放内存

每名武士都是用 `new` 创建的，生命结束时必须用 `delete` 释放，否则会发生内存泄漏：

```cpp
// warcraft1.cpp
Headquarter::~Headquarter()
{
    for (int i = 0; i < totalWarriorNum; i++)
        delete pWarriors[i];   // ①
}
```

① 遍历指针数组，逐一删除每个武士对象。析构函数会在 `Headquarter` 对象的生命期结束时（程序退出时）自动调用，不需要我们手动触发。

---

## X.4　生产武士

`Produce()` 是本题最核心的函数，整个生产逻辑都在这里。我们把它拆成两步来看。

### X.4.1　跳过造不起的武士

```cpp
// warcraft1.cpp
int Headquarter::Produce(int nTime)
{
    if (stopped)          // ①
        return 0;

    int searchingTimes = 0;
    while (Warrior::initialLifeValue[makingSeq[color][curMakingSeqIdx]]
               > totalLifeValue
           && searchingTimes < WARRIOR_NUM)    // ②
    {
        curMakingSeqIdx = (curMakingSeqIdx + 1) % WARRIOR_NUM;  // ③
        searchingTimes++;
    }
    // ...（下一小节继续）
```

① 如果已停产，直接返回 0，什么都不做。

② 这个 `while` 循环在做一件事：跳过"当前该轮到但造不起"的武士种类。`makingSeq[color][curMakingSeqIdx]` 取出当前排队的武士种类编号，拿它的生命值需求和剩余生命元比较；如果不够，就往后挪一位。条件 `searchingTimes < WARRIOR_NUM` 保证最多转一圈就停下来，不会无限循环。

③ `(curMakingSeqIdx + 1) % WARRIOR_NUM` 让索引在 0 到 4 之间循环：当它到达 4 后，下次会回到 0，就像拨号盘转圈一样。

### X.4.2　停产判断与正式生产

接着上面的代码，补上后半段：

```cpp
// warcraft1.cpp（续）
    int kindNo = makingSeq[color][curMakingSeqIdx];

    if (Warrior::initialLifeValue[kindNo] > totalLifeValue)  // ①
    {
        stopped = true;
        if (color == 0)
            printf("%03d red headquarter stops making warriors\n",  nTime);
        else
            printf("%03d blue headquarter stops making warriors\n", nTime);
        return 0;
    }

    totalLifeValue -= Warrior::initialLifeValue[kindNo];          // ②
    curMakingSeqIdx = (curMakingSeqIdx + 1) % WARRIOR_NUM;        // ③
    pWarriors[totalWarriorNum] = new Warrior(this, totalWarriorNum + 1, kindNo); // ④
    warriorNum[kindNo]++;
    pWarriors[totalWarriorNum]->PrintResult(nTime);
    totalWarriorNum++;
    return 1;                                                      // ⑤
}
```

① `while` 循环结束后，再判断一次当前武士是否造得起。如果还是不行，说明所有种类都试了一圈还是不够用，司令部宣告停产并打印消息。

> **注意：** 为什么 `while` 里不能直接判断停产，还要在循环外再判断一次？因为 `while` 的退出有两种情况：找到了造得起的武士（正常），或者转了整整一圈还不行（`searchingTimes` 到了 5）。循环本身无法区分这两种情况，所以需要循环后的 `if` 来确认。

② 确认能生产后，立刻扣减生命元。

③ `curMakingSeqIdx` 往后挪一位，下次生产从下一种武士开始排队。

④ 用 `new` 动态创建武士对象。第一个参数传 `this`，让武士知道自己属于哪个司令部；第二个参数 `totalWarriorNum + 1` 是武士编号（从 1 开始）；第三个参数是种类编号。创建完毕后立即打印降生信息。

⑤ 返回 1，告诉调用方"本轮成功生产了一名武士"。主函数会根据这个返回值判断是否应该结束模拟。

---

## X.5　辅助函数与静态成员初始化

```cpp
// warcraft1.cpp
string Headquarter::GetColor()
{
    if (color == 0) return "red";
    else            return "blue";
}

// 静态成员必须在类外定义
string Warrior::names[WARRIOR_NUM] = {"dragon", "ninja", "iceman", "lion", "wolf"};
int    Warrior::initialLifeValue[WARRIOR_NUM];   // ①

// 红方顺序：iceman(2)→lion(3)→wolf(4)→ninja(1)→dragon(0)
// 蓝方顺序：lion(3)→dragon(0)→ninja(1)→iceman(2)→wolf(4)
int Headquarter::makingSeq[2][WARRIOR_NUM] = { {2,3,4,1,0}, {3,0,1,2,4} };  // ②
```

`GetColor()` 是一个只有两行的辅助函数，把颜色整数翻译成字符串。有了它，`PrintResult()` 和 `Produce()` 就不必各自写一遍 `if (color == 0)`。

① `initialLifeValue` 在这里只是"申请内存"，数组里的值会在主函数的 `scanf` 中填入。

② `makingSeq` 是整道题最值得停下来看一眼的地方。`{2,3,4,1,0}` 翻译过来就是红方的生产顺序：kindNo 2（iceman）、3（lion）、4（wolf）、1（ninja）、0（dragon）。这样设计的好处是，用 `makingSeq[color][curMakingSeqIdx]` 就能在一行内取出当前应该生产的武士编号，查表既直观又高效。

---

## X.6　主函数：让两个司令部动起来

```cpp
// warcraft1.cpp
int main()
{
    int t, m;
    Headquarter RedHead, BlueHead;   // ①
    scanf("%d", &t);
    int nCaseNo = 1;

    while (t--)
    {
        printf("Case:%d\n", nCaseNo++);
        scanf("%d", &m);
        for (int i = 0; i < WARRIOR_NUM; i++)
            scanf("%d", &Warrior::initialLifeValue[i]);  // ②

        RedHead.Init(0, m);   // ③
        BlueHead.Init(1, m);

        int nTime = 0;
        while (true)
        {
            int tmp1 = RedHead.Produce(nTime);   // ④
            int tmp2 = BlueHead.Produce(nTime);
            if (tmp1 == 0 && tmp2 == 0)          // ⑤
                break;
            nTime++;
        }
    }
    return 0;
}
```

① `RedHead` 和 `BlueHead` 在程序启动时各创建一次，贯穿所有测试数据。每组数据开始时调用 `Init()` 重置它们，不需要反复创建和销毁。

② 静态成员可以直接用类名访问，`Warrior::initialLifeValue[i]` 把读入的值填进那张全班共享的生命值表。

③ `Init(0, m)` 传入颜色 0 代表红方，`Init(1, m)` 传入颜色 1 代表蓝方。

④ 每次循环先让红方生产，再让蓝方生产——这个顺序与题目要求的输出顺序完全一致。返回值分别存入 `tmp1` 和 `tmp2`，**不能**写成 `if (RedHead.Produce(...) == 0 && BlueHead.Produce(...) == 0)`。

> **注意：** 如果把 ⑤ 改写成 `&&` 短路求值的单行形式，当 `RedHead.Produce()` 返回 0 时，C++ 会直接认为整个条件为假，**跳过** `BlueHead.Produce()` 的调用。这样蓝方就漏掉了当轮的生产机会，输出会完全出错。用 `tmp1` 和 `tmp2` 分别接收，能保证两个司令部每轮都被调用。

⑤ 只有当两个司令部**同一轮**都没有生产（`tmp1 == 0 && tmp2 == 0`），才说明双方均已停产，模拟结束。

如果此时编译并运行程序，输入样例：

```
1
20
3 4 5 6 7
```

应该得到：

```
Case:1
000 red iceman 1 born with strength 5,1 iceman in red headquarter
000 blue lion 1 born with strength 6,1 lion in blue headquarter
001 red lion 2 born with strength 6,1 lion in red headquarter
001 blue dragon 2 born with strength 3,1 dragon in blue headquarter
002 red wolf 3 born with strength 7,1 wolf in red headquarter
002 blue ninja 3 born with strength 4,1 ninja in blue headquarter
003 red headquarter stops making warriors
003 blue iceman 4 born with strength 5,1 iceman in blue headquarter
004 blue headquarter stops making warriors
```

---

## 完整代码

```cpp
#include <iostream>
#include <cstdio>
#include <string>
using namespace std;

const int WARRIOR_NUM = 5;

class Headquarter;

class Warrior
{
    private:
        Headquarter* pHeadquarter;
        int kindNo;
        int no;
    public:
        static string names[WARRIOR_NUM];
        static int    initialLifeValue[WARRIOR_NUM];
        Warrior(Headquarter* p, int no_, int kindNo_);
        void PrintResult(int nTime);
};

class Headquarter
{
    private:
        int  totalLifeValue;
        bool stopped;
        int  totalWarriorNum;
        int  color;
        int  curMakingSeqIdx;
        int  warriorNum[WARRIOR_NUM];
        Warrior* pWarriors[1000];
    public:
        friend class Warrior;
        static int makingSeq[2][WARRIOR_NUM];
        void   Init(int color_, int lv);
        ~Headquarter();
        int    Produce(int nTime);
        string GetColor();
};

Warrior::Warrior(Headquarter* p, int no_, int kindNo_)
{
    no           = no_;
    kindNo       = kindNo_;
    pHeadquarter = p;
}

void Warrior::PrintResult(int nTime)
{
    string color = pHeadquarter->GetColor();
    printf("%03d %s %s %d born with strength %d,%d %s in %s headquarter\n",
           nTime,
           color.c_str(),
           names[kindNo].c_str(),
           no,
           initialLifeValue[kindNo],
           pHeadquarter->warriorNum[kindNo],
           names[kindNo].c_str(),
           color.c_str());
}

void Headquarter::Init(int color_, int lv)
{
    color           = color_;
    totalLifeValue  = lv;
    totalWarriorNum = 0;
    stopped         = false;
    curMakingSeqIdx = 0;
    for (int i = 0; i < WARRIOR_NUM; i++)
        warriorNum[i] = 0;
}

Headquarter::~Headquarter()
{
    for (int i = 0; i < totalWarriorNum; i++)
        delete pWarriors[i];
}

int Headquarter::Produce(int nTime)
{
    if (stopped)
        return 0;

    int searchingTimes = 0;
    while (Warrior::initialLifeValue[makingSeq[color][curMakingSeqIdx]]
               > totalLifeValue
           && searchingTimes < WARRIOR_NUM)
    {
        curMakingSeqIdx = (curMakingSeqIdx + 1) % WARRIOR_NUM;
        searchingTimes++;
    }

    int kindNo = makingSeq[color][curMakingSeqIdx];

    if (Warrior::initialLifeValue[kindNo] > totalLifeValue)
    {
        stopped = true;
        if (color == 0)
            printf("%03d red headquarter stops making warriors\n",  nTime);
        else
            printf("%03d blue headquarter stops making warriors\n", nTime);
        return 0;
    }

    totalLifeValue -= Warrior::initialLifeValue[kindNo];
    curMakingSeqIdx = (curMakingSeqIdx + 1) % WARRIOR_NUM;
    pWarriors[totalWarriorNum] = new Warrior(this, totalWarriorNum + 1, kindNo);
    warriorNum[kindNo]++;
    pWarriors[totalWarriorNum]->PrintResult(nTime);
    totalWarriorNum++;
    return 1;
}

string Headquarter::GetColor()
{
    if (color == 0) return "red";
    else            return "blue";
}

string Warrior::names[WARRIOR_NUM] = {"dragon", "ninja", "iceman", "lion", "wolf"};
int    Warrior::initialLifeValue[WARRIOR_NUM];
int    Headquarter::makingSeq[2][WARRIOR_NUM] = { {2,3,4,1,0}, {3,0,1,2,4} };

int main()
{
    int t, m;
    Headquarter RedHead, BlueHead;
    scanf("%d", &t);
    int nCaseNo = 1;

    while (t--)
    {
        printf("Case:%d\n", nCaseNo++);
        scanf("%d", &m);
        for (int i = 0; i < WARRIOR_NUM; i++)
            scanf("%d", &Warrior::initialLifeValue[i]);

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
