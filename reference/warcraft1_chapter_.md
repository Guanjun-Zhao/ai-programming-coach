# 第 1 章　用类建模：魔兽世界备战

在本章中，我们将解决一道经典的面向对象建模题——魔兽世界备战。题目要求模拟两个司令部按固定顺序循环生产武士，直到生命元耗尽为止，并按时间顺序打印每一个事件。

这道题本身并不复杂，但如果一开始就用全局变量各写一套，你会发现红方和蓝方的代码几乎是完全相同的复制——只有几个数字不同。用类封装之后，两个司令部只是同一套逻辑的两个实例，主函数会变得出奇地简洁。在本章中，你将学会定义 `Warrior` 和 `Headquarter` 两个相互关联的类，以及在 C++ 中处理类之间相互引用时用到的**前向声明**技术。

## 1.1　规划程序

在动手写代码之前，先来梳理程序要做的事：从第 0 小时开始，每小时让红方先、蓝方后各尝试生产一名武士；如果当前该造的武士造不起，就顺移到下一种；五种都造不起则宣告停产；双方都停产后本组数据结束。

据此可以确定核心分工：`Warrior` 负责记录自身属性并打印降生信息，`Headquarter` 负责管理生命元和生产顺序，主函数只需让两个司令部对象轮流调用 `Produce()` 就够了。

## 1.2　创建 Warrior 类

### 1.2.1　类的声明

下面来创建 `warcraft1.cpp`，先写好文件开头和 `Warrior` 类的声明：

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
        static string names[WARRIOR_NUM];           // ③
        static int initialLifeValue[WARRIOR_NUM];   // ③
        Warrior(Headquarter* p, int no_, int kindNo_);
        void PrintResult(int nTime);
};
```

在①处只写了一行 `class Headquarter;`，这叫**前向声明**。`Warrior` 类内部需要保存一个指向 `Headquarter` 的指针（见②），但 `Headquarter` 的完整定义还没出现。好在编译器只需知道"这是个类的名字"就能处理指针，不需要知道类里有什么，所以一行前向声明就够了。

在②处，每名武士都持有指向自己所属司令部的指针 `pHeadquarter`。武士打印降生消息时需要查询司令部的颜色和该类武士的现有数量，这个指针是唯一的通道。

③处的两个成员前面有 `static` 关键字，意味着它们属于整个类，而不属于某一个武士对象。无论创建了多少名武士，名字表 `names` 和生命值表 `initialLifeValue` 在内存里只有一份，所有武士都从这里读取自己的属性。

> **注意：** 静态成员变量必须在类外单独定义，否则编译能通过、链接会出错。你会在 X.5 节看到定义它们的三行代码。

### 1.2.2　构造函数

接下来实现 `Warrior` 的构造函数：

```cpp
// warcraft1.cpp
--snip--
Warrior::Warrior(Headquarter* p, int no_, int kindNo_)
{
    no           = no_;      // ①
    kindNo       = kindNo_;
    pHeadquarter = p;        // ②
}
```

在①处，参数名比成员名多了一个下划线，这是 C++ 里常见的惯例——如果参数和成员同名，赋值语句 `no = no` 不会出错，但两边指的是同一个变量，什么也没赋到。多一个下划线就消除了这种歧义。

在②处，把司令部地址存进 `pHeadquarter`，武士从此刻起就"认识"自己的主人了。

### 1.2.3　打印降生消息

每当一名武士诞生，就要立刻打印一条消息。下面来实现 `PrintResult()`：

```cpp
// warcraft1.cpp
--snip--
void Warrior::PrintResult(int nTime)
{
    string color = pHeadquarter->GetColor();   // ①
    printf("%03d %s %s %d born with strength %d,%d %s in %s headquarter\n",
           nTime,
           color.c_str(),                        // ②
           names[kindNo].c_str(),
           no,
           initialLifeValue[kindNo],
           pHeadquarter->warriorNum[kindNo],     // ③
           names[kindNo].c_str(),
           color.c_str());
}
```

在①处调用 `pHeadquarter->GetColor()`，把颜色整数翻译成 `"red"` 或 `"blue"`，这个方法我们稍后在 `Headquarter` 中实现。

在②处调用 `c_str()`，把 C++ 的 `string` 转成 C 风格的字符指针——`printf` 不直接认识 `string` 类型，必须做这个转换。

在③处直接读取了 `pHeadquarter->warriorNum[kindNo]`，这是 `Headquarter` 的私有成员。之所以能这样做，是因为我们稍后会在 `Headquarter` 里写一行 `friend class Warrior`，声明武士是司令部的"友元"，允许它访问私有数据。

> **注意：** `%03d` 的含义：`%d` 输出整数，`3` 表示最少显示 3 位，`0` 表示不足的位数用 0 补齐。数字 7 会输出为 `007`，数字 42 会输出为 `042`。这正是题目要求的时间格式。

## 1.3　创建 Headquarter 类

### 1.3.1　类的声明

下面来定义 `Headquarter` 类：

```cpp
// warcraft1.cpp
--snip--
class Headquarter
{
    private:
        int  totalLifeValue;             // ①
        bool stopped;                    // ②
        int  totalWarriorNum;
        int  color;                      // ③
        int  curMakingSeqIdx;            // ④
        int  warriorNum[WARRIOR_NUM];    // ⑤
        Warrior* pWarriors[1000];
    public:
        friend class Warrior;                       // ⑥
        static int makingSeq[2][WARRIOR_NUM];       // ⑦
        void   Init(int color_, int lv);
        ~Headquarter();
        int    Produce(int nTime);
        string GetColor();
};
```

①中的 `totalLifeValue` 是剩余生命元，每生产一名武士就扣减一次。②中的 `stopped` 是一个开关：一旦置为 `true`，以后每次调用 `Produce()` 都立即返回，不再做任何计算。

在③处，`color` 用 0 代表红方、1 代表蓝方。用整数而非字符串，是为了方便在⑦的数组里当下标使用。

在④处，`curMakingSeqIdx` 是一个在 0 到 4 之间循环的索引，记录"下一个该轮到哪种武士"。

在⑤处，`warriorNum` 记录各类武士已生产的数量，`PrintResult()` 打印时需要读这里。

在⑥处声明 `friend class Warrior`，打开了一扇让武士访问司令部私有数据的小门。

在⑦处，`makingSeq` 是一个 2×5 的静态数组，第一维是阵营，第二维是顺序，每个元素存储武士的 `kindNo`——相当于把题目里的"生产顺序"硬编码成一张查找表。

### 1.3.2　初始化方法

题目有多组测试数据，同一对司令部对象需要反复重置。我们专门写一个 `Init()` 方法来做这件事：

```cpp
// warcraft1.cpp
--snip--
void Headquarter::Init(int color_, int lv)
{
    color           = color_;
    totalLifeValue  = lv;
    totalWarriorNum = 0;
    stopped         = false;          // ①
    curMakingSeqIdx = 0;
    for (int i = 0; i < WARRIOR_NUM; i++)
        warriorNum[i] = 0;            // ②
}
```

在①处，每组数据开始时司令部从"未停产"状态重新出发。

在②处，各类武士的计数清零，否则上一组数据的数字会带到下一组里去，输出就全错了。

> **注意：** 这里用 `Init()` 而非构造函数，因为 C++ 的构造函数只在对象创建时调用一次，之后就不能再调了。`Init()` 是一个普通方法，可以在每组测试数据开始时反复调用，适合处理多组输入的题目。

### 1.3.3　析构函数

每名武士都是用 `new` 创建的，程序结束前需要逐一 `delete`：

```cpp
// warcraft1.cpp
--snip--
Headquarter::~Headquarter()
{
    for (int i = 0; i < totalWarriorNum; i++)
        delete pWarriors[i];   // ①
}
```

在①处，遍历指针数组，依次释放每个武士占用的内存。规则很简单：`new` 出来的东西，最终必须 `delete`，否则就是内存泄漏。析构函数会在对象生命期结束时（程序退出时）自动被调用。

## 1.4　让司令部生产武士

`Produce()` 是整个程序最关键的方法，我们分两步来看。

### 1.4.1　跳过造不起的武士

```cpp
// warcraft1.cpp
--snip--
int Headquarter::Produce(int nTime)
{
    if (stopped)        // ①
        return 0;

    int searchingTimes = 0;
    while (Warrior::initialLifeValue[makingSeq[color][curMakingSeqIdx]]
               > totalLifeValue
           && searchingTimes < WARRIOR_NUM)   // ②
    {
        curMakingSeqIdx = (curMakingSeqIdx + 1) % WARRIOR_NUM;   // ③
        searchingTimes++;
    }
    --snip--
```

在①处，如果 `stopped` 已经为 `true`，直接返回 0——停产后的司令部每次被调用都立即跳过，不浪费任何时间。

在②处，`while` 循环负责"跳过当前造不起的武士"。`makingSeq[color][curMakingSeqIdx]` 取出当前该轮到的武士种类编号，拿它的生命值和剩余生命元比较；如果不够，就把索引往后移一位，`searchingTimes` 加一。条件 `searchingTimes < WARRIOR_NUM` 保证最多转一整圈就停下来，不会无限循环。

在③处，`(curMakingSeqIdx + 1) % WARRIOR_NUM` 让索引在 0 到 4 之间循环——当索引到达 4 后，下一次会回到 0，就像钟表的表针一样。

### 1.4.2　停产判断与正式生产

接上一小节，把 `Produce()` 补全：

```cpp
// warcraft1.cpp（接上）
    --snip--
    int kindNo = makingSeq[color][curMakingSeqIdx];

    if (Warrior::initialLifeValue[kindNo] > totalLifeValue)   // ①
    {
        stopped = true;
        if (color == 0)
            printf("%03d red headquarter stops making warriors\n",  nTime);
        else
            printf("%03d blue headquarter stops making warriors\n", nTime);
        return 0;
    }

    totalLifeValue -= Warrior::initialLifeValue[kindNo];                   // ②
    curMakingSeqIdx = (curMakingSeqIdx + 1) % WARRIOR_NUM;
    pWarriors[totalWarriorNum] = new Warrior(this, totalWarriorNum+1, kindNo);  // ③
    warriorNum[kindNo]++;
    pWarriors[totalWarriorNum]->PrintResult(nTime);
    totalWarriorNum++;
    return 1;   // ④
}
```

在①处，`while` 循环结束后需要再判断一次。这是因为循环有两种退出方式：找到了造得起的武士（正常），或者转了整整一圈还是不够（`searchingTimes` 到了 5）。循环本身无法区分这两种情况，所以循环后的 `if` 才能确认"真的所有种类都造不了"。一旦确认，就把 `stopped` 置为 `true` 并打印停产消息。

在②处，扣减生命元，同时推进 `curMakingSeqIdx`——下次生产从下一种武士开始排队。

在③处，用 `new` 创建武士对象，第一个参数传 `this`，让这名武士知道自己是哪个司令部生产的；`totalWarriorNum+1` 是武士编号（从 1 开始计数）。创建完后立即调用 `PrintResult()` 打印降生消息。

在④处返回 1，告诉主函数"本轮成功生产了一名武士"。这个返回值很重要，主函数靠它判断是否所有司令部都已停产。

## 1.5　辅助函数与静态成员初始化

现在来补上 `GetColor()` 和三行静态成员的定义：

```cpp
// warcraft1.cpp
--snip--
string Headquarter::GetColor()
{
    if (color == 0) return "red";
    else            return "blue";
}

string Warrior::names[WARRIOR_NUM] = {"dragon","ninja","iceman","lion","wolf"};  // ①
int    Warrior::initialLifeValue[WARRIOR_NUM];   // ②

// 红方顺序：iceman(2)→lion(3)→wolf(4)→ninja(1)→dragon(0)
// 蓝方顺序：lion(3)→dragon(0)→ninja(1)→iceman(2)→wolf(4)
int Headquarter::makingSeq[2][WARRIOR_NUM] = { {2,3,4,1,0}, {3,0,1,2,4} };  // ③
```

`GetColor()` 只有两行，却被好几处代码调用，专门写成一个方法可以避免到处重复写 `if (color == 0)`。

在①处，`names` 初始化了五种武士的名字，顺序与 `kindNo` 对应：0=dragon，1=ninja，2=iceman，3=lion，4=wolf。

在②处，`initialLifeValue` 只是申请了内存，真正的值会在主函数里通过 `scanf` 逐个填入。

在③处是 `makingSeq` 的初始化，这是整道题最值得停下来看一眼的地方。`{2,3,4,1,0}` 就是红方的生产顺序：kindNo 2（iceman）→3（lion）→4（wolf）→1（ninja）→0（dragon）；`{3,0,1,2,4}` 是蓝方的顺序。把文字顺序翻译成编号序列，之后用 `makingSeq[color][curMakingSeqIdx]` 就能一步取到当前该生产哪种武士。

## 1.6　主函数

下面来写主函数，把所有部件组装起来：

```cpp
// warcraft1.cpp
--snip--
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
            scanf("%d", &Warrior::initialLifeValue[i]);   // ②

        RedHead.Init(0, m);    // ③
        BlueHead.Init(1, m);

        int nTime = 0;
        while (true)
        {
            int tmp1 = RedHead.Produce(nTime);    // ④
            int tmp2 = BlueHead.Produce(nTime);
            if (tmp1 == 0 && tmp2 == 0)           // ⑤
                break;
            nTime++;
        }
    }
    return 0;
}
```

在①处，`RedHead` 和 `BlueHead` 在程序启动时各创建一次，贯穿整个运行过程，每组数据用 `Init()` 重置即可（见③）。

在②处，静态成员可以直接用类名访问：`Warrior::initialLifeValue[i]` 把读入的五个值填进那张全员共享的生命值表，之后所有武士对象都能读到它们。

在③处，`Init(0, m)` 传入颜色 0 表示红方，`Init(1, m)` 传入颜色 1 表示蓝方。

在④处，每次循环先让红方生产、再让蓝方生产，顺序与题目的输出要求完全一致。这里特意用 `tmp1` 和 `tmp2` 分别接收返回值，而不是直接写 `if (RedHead.Produce(...) == 0 && BlueHead.Produce(...) == 0)`。

> **注意：** 如果把⑤写成一行 `&&` 的形式，C++ 的短路求值规则会导致：当 `RedHead.Produce()` 返回 0 时，右侧的 `BlueHead.Produce()` 根本不会被执行——蓝方就漏掉了当轮的生产机会，输出将完全出错。用 `tmp1` 和 `tmp2` 分开接收，就能保证两个司令部每轮都被调用到。

在⑤处，只有当同一轮内两个司令部都返回 0，才说明双方均已停产，循环退出。

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
000 blue lion 1 born with strength 6,1 lion in blue headquarter
001 red lion 2 born with strength 6,1 lion in red headquarter
001 blue dragon 2 born with strength 3,1 dragon in blue headquarter
002 red wolf 3 born with strength 7,1 wolf in red headquarter
002 blue ninja 3 born with strength 4,1 ninja in blue headquarter
003 red headquarter stops making warriors
003 blue iceman 4 born with strength 5,1 iceman in blue headquarter
004 blue headquarter stops making warriors
```
