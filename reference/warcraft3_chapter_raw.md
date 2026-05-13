# 第 3 章　开战：移动、战斗与事件驱动

在前两章里，武士只需要"降生"，程序随后立刻打印结果。这一章的世界大不相同——武士要在城市之间行军、相遇后要交战、lion 可能临阵逃跑、iceman 每走一步都会损失生命值，而所有这些事件都必须按时间和地点排好顺序再统一输出。

事件的总数和顺序无法在发生时就确定，因此我们引入一个全新的设计思路：把所有发生的事件先收集起来，最后一次性排序输出。这就是本章的核心——**事件驱动架构**。与此同时，武器从上一章的简单数据升级为拥有各自行为的类，战斗逻辑也需要单独的方法来承载。

本章新增的类和方法很多，但每一处都是为了解决一个具体问题。我们依然从"规划"入手，逐步添加各个模块。

## 3.1　规划新功能

与上一章相比，这次的改动分为四个方向：

第一，引入 `CKingdom` 类作为整个世界的"指挥官"，它持有红蓝两个司令部，按分钟推进时间，并在内部收集所有事件，最后排序输出。第二，引入 `CEvent` 类描述一条事件记录，重载 `operator<` 定义排序规则。第三，把上一章的 `CWeapon` 改造为继承体系：基类负责接口，`CSWord`、`CArrow`、`CBomb` 三个子类各自实现不同的攻击逻辑。第四，大幅扩展 `CWarrior`：武士现在拥有一组武器、当前位置和攻击力，并实现 `March()`、`Attack()`、`FightBack()` 等方法，各子类再按需覆盖特有行为。

主函数和 `CHeadquarter` 的整体结构保留，但 `CHeadquarter` 内部的武士容器从数组改为 `list`，并增加了大量战场管理方法。

## 3.2　事件驱动：`CEvent` 与 `CKingdom`

### 3.2.1　`CEvent` 类的声明

所有发生的事情都被包装成一个 `CEvent` 对象，暂存在 `CKingdom` 的 `vEvent` 向量里，最后统一排序输出。先来写好 `CEvent` 的成员变量和函数声明：

```cpp
// warcraft3.cpp
enum EEventType { EVENT_BORN, EVENT_LION_RUN, EVENT_MARCH, EVENT_WOLFSROB,
                  EVENT_FIGHT_RESULT, EVENT_YELL, EVENT_EARNMONEY,
                  EVENT_REACH, EVENT_CITYTAKEN, EVENT_PRINTMONEY,
                  EVENT_WARRIOR_REPORT };   // ①

class CEvent
{
private:
    EEventType eEventType;   // ②
    int nTime;
    int nCityNo;
    int nColor;
    string sDescribe;
public:
    CEvent(EEventType eEventType_, int nTime_, int nCityNo_,
           int nColor_, const string & s) :
        eEventType(eEventType_), nTime(nTime_),
        nCityNo(nCityNo_), nColor(nColor_), sDescribe(s) {}   // ③
    void Output();
    bool operator<(const CEvent & e2) const;
};
```

在①处，`EEventType` 枚举列出了程序中所有可能的事件类型——降生、lion逃跑、行军、wolf抢武器、战斗结果等。枚举值的**声明顺序就是同地同时事件的优先级**：值越小越先输出。

在②处，每条事件记录保存了五个字段：事件类型、发生时间（分钟数）、发生城市、所属阵营，以及描述字符串。

在③处，构造函数只有**成员初始化列表**，函数体为空 `{}`。C++ 推荐用初始化列表而非函数体内赋值来初始化成员——前者在成员被创建时直接初始化，不会多做一次默认构造。`Output()` 和 `operator<` 只写了声明，函数体在下面两节分别补上。

### 3.2.2　格式化输出：`Output()`

`Output()` 负责把一条事件记录打印出来，并按题目格式把分钟数转成"时:分"：

```cpp
// warcraft3.cpp
--snip--
void CEvent::Output()
{
    char szTime[20];
    sprintf(szTime, "%03d:%02d", nTime / 60, nTime % 60);   // ①
    cout << szTime << " " << sDescribe << endl;
}
```

在①处，把内部存储的分钟数拆成小时（整除 60）和剩余分钟（取模 60），用 `%03d:%02d` 格式化后拼入输出字符串。

### 3.2.3　排序规则：`operator<`

`operator<` 定义了两条事件比较大小的规则，`sort` 函数依赖它来排序：

```cpp
// warcraft3.cpp
--snip--
bool CEvent::operator<(const CEvent & e2) const
{
    if (nTime != e2.nTime)           return nTime < e2.nTime;           // ①
    if (nCityNo != e2.nCityNo)       return nCityNo < e2.nCityNo;       // ②
    if (eEventType != e2.eEventType) return eEventType < e2.eEventType; // ③
    return nColor < e2.nColor;                                           // ④
}
```

在①处，最优先按时间排——早发生的排前面。

在②处，同一时刻按城市编号从小到大（即从西到东）排。

在③处，同城同时的事件按类型排——这正是 `EEventType` 枚举声明顺序的意义：`EVENT_LION_RUN` 的值比 `EVENT_MARCH` 小，所以 lion 逃跑先于行军打印。

在④处，最后按阵营排，红方（0）排在蓝方（1）之前。

### 3.2.4　`CKingdom` 类的声明

`CKingdom` 是整个模拟的驱动核心，它持有两个司令部，按分钟逐步推进时间。先来写好它的成员变量和函数声明：

```cpp
// warcraft3.cpp
--snip--
class CKingdom
{
    friend class CHeadquarter;
private:
    CHeadquarter Red, Blue;    // ①
    int nTimeInMinutes;
    vector<CEvent> vEvent;     // ②
    int nEndTime;
    int nCityNum;
public:
    CKingdom(int nCityNum_, int nInitMoney);
    void Run(int T);
    int  TimePass(int nMinutes);         // ③
    void OutputResult();
    void AddEvent(EEventType eType, int nCityNo, int nColor, const string & s);
    void WarEnd();
};
```

在①处，红蓝司令部作为 `CKingdom` 的**成员对象**直接嵌入，不是指针，也不是动态分配。

在②处，`vEvent` 向量负责收集所有事件；整个模拟过程中，所有 `AddEvent()` 调用都把事件追加到这里，直到最后再排序。

在③处，`public` 区域只列出成员函数的**声明**——每个函数的具体实现依次在下面几节展开。`TimePass` 是最关键的方法，负责按分钟调度所有动作，单独用一节讲解。

### 3.2.5　`CKingdom` 构造函数

构造函数负责初始化两个司令部并建立它们之间的连接：

```cpp
// warcraft3.cpp
--snip--
CKingdom::CKingdom(int nCityNum_, int nInitMoney) :
    nTimeInMinutes(0),
    Red(COLOR_RED,  nInitMoney, 0),
    Blue(COLOR_BLUE, nInitMoney, nCityNum_ + 1),   // ①
    nCityNum(nCityNum_)
{
    Red.SetKingdom(this);   Red.SetEnemy(&Blue);
    Blue.SetKingdom(this);  Blue.SetEnemy(&Red);   // ②
    nEndTime = 3000000;
}
```

在①处，红方司令部城市编号为 0，蓝方为 `nCityNum + 1`，分别位于世界的两端。

在②处，函数体里让两个司令部相互认识：每个司令部都持有指向 `CKingdom` 的指针（用于调用 `AddEvent`）和指向对方的指针（用于查询敌情）。两个调用完成后，整个模拟世界才真正"连通"。

### 3.2.6　`Run()`、`OutputResult()` 等辅助方法

下面来实现 `CKingdom` 的其余四个辅助方法，它们各司其职，共同构成模拟的外层框架：

```cpp
// warcraft3.cpp
--snip--
void CKingdom::Run(int T) {
    for (int t = 0; t <= T; t++)
        if (TimePass(t) == 0) return;   // ①
}

void CKingdom::OutputResult() {
    sort(vEvent.begin(), vEvent.end());   // ②
    for (int i = 0; i < vEvent.size(); i++)
        vEvent[i].Output();
}

void CKingdom::AddEvent(EEventType eType, int nCityNo,
                        int nColor, const string & s) {
    CEvent tmp(eType, nTimeInMinutes, nCityNo, nColor, s);
    vEvent.push_back(tmp);   // ③
}

void CKingdom::WarEnd() {
    if (nEndTime == 3000000) nEndTime = nTimeInMinutes;   // ④
}
```

在①处，`Run(T)` 从第 0 分钟逐分钟推进到第 T 分钟，只要 `TimePass` 返回 0（战争结束），就立即停止。

在②处，`OutputResult()` 利用 `operator<` 对 `vEvent` 排序后逐条输出——所有事件在这一刻才真正打印，这就是事件驱动架构的核心：**先收集，后排序，再输出**。

在③处，`AddEvent()` 是一个转发函数：它把调用方提供的参数和当前时间打包成 `CEvent` 对象，追加到 `vEvent` 末尾。所有模块通过这个方法添加事件，而不是直接操作 `vEvent`。

在④处，`WarEnd()` 只记录**第一次**战争结束的时间——用 `3000000` 作为"尚未结束"的哨兵值，大于任何合法的模拟时间。

### 3.2.7　`TimePass()`

下面来实现 `TimePass()`，它是整个时间轴的调度中心：

```cpp
// warcraft3.cpp
--snip--
int CKingdom::TimePass(int nMinutes) {
    nTimeInMinutes = nMinutes;
    if (nTimeInMinutes > nEndTime) return 0;   // ①
    int nRemain = nTimeInMinutes % 60;
    switch (nRemain) {
        case  0: Red.WarriorBorn();    Blue.WarriorBorn();    break;  // ②
        case  5: Red.LionRunaway();    Blue.LionRunaway();    break;
        case 10: Red.WarriorsMarch(nCityNum + 1);
                 Blue.WarriorsMarch(0);                       break;
        case 35: Red.WolfsRob();       Blue.WolfsRob();       break;
        case 40: Red.WarriorsAttack(); Blue.WarriorsAttack(); break;
        case 50: Red.PrintMoney();     Blue.PrintMoney();     break;
        case 55: Red.WarriorsReport(); Blue.WarriorsReport(); break;
    }
    return 1;
}
```

在①处，若当前时间已超过战争结束时刻，直接返回 0 停止循环。

在②处，每小时有七个时间点触发不同动作：整点造兵、第 5 分 lion 逃跑、第 10 分行军、第 35 分 wolf 抢武器、第 40 分战斗、第 50 分司令部报告生命元、第 55 分武士报告武器情况。题目的所有逻辑都汇聚在这一张时间表里，新增规则只需在对应分钟增加调用即可。

## 3.3　武器的继承体系

### 3.3.1　`CWeapon` 类的声明

上一章的 `CWeapon` 只是一个数据容器。这一章三种武器的攻击逻辑各不相同，因此 `CWeapon` 升级为含有纯虚函数的基类。先来写好它的声明：

```cpp
// warcraft3.cpp
--snip--
class CWeapon
{
public:
    int nKindNo;
    CWarrior * master;                              // ①
    static const char * Names[WEAPON_NUM];

    CWeapon(CWarrior * m) : master(m) {}
    virtual int GetForce() = 0;                     // ②
    virtual int Attack(CWarrior * pEnemy);          // ③
    static CWeapon * NewWeapon(int idx, CWarrior * master);  // ④
};
```

在①处，每件武器持有一个指向拥有者（`master`）的指针——因为攻击力是拥有者当前攻击力的百分比，计算时需要回查。

在②处，`GetForce()` 声明为纯虚，三个子类各自给出计算公式。

在③处，`Attack()` 提供默认实现，下一节补上函数体。

在④处，`NewWeapon()` 是一个静态工厂方法，接受编号返回对应子类指针，调用方无需关心具体类型。

### 3.3.2　默认攻击行为：`Attack()`

基类的 `Attack()` 给出所有武器共用的默认攻击逻辑：

```cpp
// warcraft3.cpp
--snip--
int CWeapon::Attack(CWarrior * pEnemy) {
    pEnemy->Hurted(GetForce());
    return 1;   // ①
}
```

在①处，返回值有三种含义：0 表示武器已消耗完毕（调用方应立即 `delete`），1 表示状态未改变，2 表示武器被使用但状态发生了改变——三个子类会按需覆盖这一行为。

### 3.3.3　`CSWord`：剑

下面来实现三种武器子类，先从最简单的 `CSWord` 开始：

```cpp
// warcraft3.cpp
--snip--
class CSWord : public CWeapon
{
public:
    virtual int GetForce() {
        return master->GetForce() * 2 / 10;   // ①
    }
    CSWord(CWarrior * m) : CWeapon(m) { nKindNo = 0; }
};
```

在①处，剑的攻击力是拥有者当前攻击力的 20%，用整数乘法 `* 2 / 10` 避免浮点误差。`CSWord` 没有任何额外状态，每次攻击都能使用，不会被消耗。

### 3.3.4　`CArrow`：使用计数

`CArrow`（箭）需要额外记录被使用的次数——用完两次之后就会消耗掉：

```cpp
// warcraft3.cpp
--snip--
class CArrow : public CWeapon
{
    int usedTimes;
public:
    virtual int GetForce() {
        return master->GetForce() * 3 / 10;   // ①
    }
    CArrow(CWarrior * master) : CWeapon(master), usedTimes(0) { nKindNo = 2; }
    virtual int Attack(CWarrior * pEnemy) {
        CWeapon::Attack(pEnemy);
        ++usedTimes;
        if (usedTimes == 2) return 0;   // ②
        return 2;
    }
};
```

在①处，箭的攻击力是拥有者攻击力的 30%，同样写成整数乘法 `* 3 / 10`。

在②处，箭被使用两次后返回 0，调用方会 `delete` 这支箭并将指针置 `NULL`。

### 3.3.5　`CBomb`：自爆伤害

`CBomb`（炸弹）最为特殊——爆炸时使用者本身也会受到伤害：

```cpp
// warcraft3.cpp
--snip--
class CBomb : public CWeapon
{
public:
    virtual int GetForce() {
        return master->GetForce() * 4 / 10;   // ①
    }
    CBomb(CWarrior * master) : CWeapon(master) { nKindNo = 1; }
    virtual int Attack(CWarrior * pEnemy) {
        int force = GetForce();
        if (master->GetName().find("ninja") == string::npos)
            master->Hurted(force / 2);   // ②
        pEnemy->Hurted(force);
        return 0;   // ③
    }
};
```

在①处，炸弹攻击力是拥有者攻击力的 40%。

在②处，炸弹爆炸时使用者也会受到伤害（伤害值为炸弹攻击力的一半）——但 ninja 天生免疫自伤，所以先检查 `master` 的名字是否包含 `"ninja"`。

在③处，炸弹一次性消耗，返回 0 表示立即删除。

> **注意：** 题目明确要求"去尾取整"的除法不要用浮点数（`force * 0.3` 在不同编译器下可能得到 `14` 或 `15`），必须写整数乘法再整除：`force * 3 / 10`。

### 3.3.6　工厂方法 `NewWeapon()`

工厂方法 `NewWeapon()` 把三种子类的创建集中在一处：

```cpp
// warcraft3.cpp
--snip--
CWeapon * CWeapon::NewWeapon(int idx, CWarrior * master)
{
    switch (idx) {
        case 0: return new CSWord(master);
        case 1: return new CBomb(master);
        case 2: return new CArrow(master);
    }
    return NULL;
}
```

武士子类的构造函数只需调用 `CWeapon::NewWeapon(nId % 3, this)` 就能得到正确类型的武器对象，不必关心是剑、炸弹还是箭。

## 3.4　扩展 `CWarrior`：移动与战斗

### 3.4.1　新字段

`CWarrior` 在本章新增了位置、攻击力、武器数组等字段，并声明了 `Runaway()`、`Yell()` 等可供子类覆盖的虚函数。先来写好类的声明：

```cpp
// warcraft3.cpp
--snip--
class CWarrior
{
public:
    static const int MAX_WPS = 10;
protected:
    int nStrength;
    int nForce;
    int nCityNo;       // ①
    int nId;
    int weaponIdx;     // ②
    CHeadquarter * pHeadquarter;
    CWeapon * weapons[MAX_WPS];   // ③
public:
    static const char * Names[WARRIOR_NUM];
    static int InitialLifeValue[WARRIOR_NUM];
    static int InitalForce[WARRIOR_NUM];

    virtual bool Runaway() { return false; }   // ④
    virtual string Yell()  { return ""; }

    CWarrior(int nId_, int nStrength_, int nForce_, int nCityNo_,
             CHeadquarter * pHeadquarter_);
    virtual ~CWarrior();
    virtual string GetName() = 0;
    virtual void March();
    void SortWeapons(bool forTaken = false);
    int  Attack(CWarrior * pEnemy);
    void FightBack(CWarrior * pEnemy);
    string TakeEnemyWeapons(CWarrior * pEnemy, bool beforeFight = false);
};
```

在①处，`nCityNo` 记录武士当前所在城市编号，红方从 0 出发向右走，蓝方从 `N+1` 出发向左走。

在②处，`weaponIdx` 是武器循环使用的游标——每次 `FightBack` 时从这里找到下一件可用武器。

在③处，`weapons[MAX_WPS]` 最多持有 10 件武器，不用的槽位保持 `NULL`。

在④处，`Runaway()` 和 `Yell()` 有默认实现（返回 `false`/空字符串），只有 lion 和 dragon 需要覆盖，其他子类无需理会。构造函数、析构函数和各战斗方法只写了声明，函数体在后面各节逐一补上。

### 3.4.2　构造函数与析构函数

构造函数初始化所有字段并把武器数组清零；析构函数负责释放动态分配的武器对象：

```cpp
// warcraft3.cpp
--snip--
CWarrior::CWarrior(int nId_, int nStrength_, int nForce_, int nCityNo_,
                   CHeadquarter * pHeadquarter_) :
    nId(nId_), nStrength(nStrength_), nForce(nForce_),
    nCityNo(nCityNo_), pHeadquarter(pHeadquarter_), weaponIdx(0)
{
    memset(weapons, 0, sizeof(weapons));   // ①
}

CWarrior::~CWarrior() {
    for (int i = 0; i < MAX_WPS; ++i)
        if (weapons[i]) delete weapons[i];   // ②
}
```

在①处，`memset` 把武器数组全部初始化为 `NULL`，避免野指针——武器是按需通过 `NewWeapon()` 创建后挂入数组的，不能让空槽位残留随机值。

在②处，遍历武器数组，依次释放每个武士持有的武器。规则和上一章一样：`new` 出来的东西最终必须 `delete`，析构函数在武士对象生命期结束时自动被调用。

### 3.4.3　`March()`：移动逻辑

`March()` 在每小时第 10 分钟被调用，武士向对方方向前进一步：

```cpp
// warcraft3.cpp
--snip--
void CWarrior::March()
{
    if (GetColor() == COLOR_RED) nCityNo++;   // ①
    else                          nCityNo--;
    weaponIdx = 0;   // ②
}
```

在①处，`March()` 根据颜色决定移动方向：红方城市编号加一，蓝方减一。

在②处，每次行军后将 `weaponIdx` 归零，使武器轮次从头开始——题目规定战斗开始前先重新排好武器顺序再使用。

### 3.4.4　排序武器

武器在战斗前和被缴获时需要按不同规则排序：

```cpp
// warcraft3.cpp
--snip--
int WpCompare(const void *wp1, const void *wp2)   // ①
{
    CWeapon **p1 = (CWeapon **)wp1;
    CWeapon **p2 = (CWeapon **)wp2;
    if (*p1 == NULL) return  1;   // ②
    if (*p2 == NULL) return -1;
    if ((*p1)->nKindNo != (*p2)->nKindNo)
        return (*p1)->nKindNo - (*p2)->nKindNo;   // ③
    if ((*p1)->nKindNo == WEAPON_ARROW)
        return ((CArrow *)(*p2))->usedTimes
             - ((CArrow *)(*p1))->usedTimes;      // ④
    return 0;
}

void CWarrior::SortWeapons(bool forTaken)
{
    if (forTaken)
        qsort(weapons, MAX_WPS, sizeof(CWeapon *), WpCompare2);   // ⑤
    else
        qsort(weapons, MAX_WPS, sizeof(CWeapon *), WpCompare);
}
```

在①处，`WpCompare` 是传递给 `qsort` 的比较函数，参数类型固定为 `const void *`。

在②处，`NULL` 槽位排到最后——把所有非空武器都集中到数组前段，方便遍历。

在③处，主排序键是武器种类编号：sword(0) < bomb(1) < arrow(2)。

在④处，对于 arrow，把**用过次数少的排前面**（即新箭优先使用）。

在⑤处，`WpCompare2` 与 `WpCompare` 的区别是 arrow 排序方向相反——缴获敌方武器时，优先缴获**没用过的箭**（用过 0 次的先缴）。`forTaken = true` 时使用这个规则。

### 3.4.5　`Attack()`：循环使用武器

攻击方把自己所有武器轮流用一遍，每用一件后让对方还击：

```cpp
// warcraft3.cpp
--snip--
int CWarrior::Attack(CWarrior * pEnemy)
{
    if (nStrength <= 0 || pEnemy->GetStrength() <= 0)
        return 0;
    while (true) {
        bool validAttack = false;
        for (int i = 0; i < MAX_WPS; ++i) {
            int tmps = pEnemy->GetStrength();   // ①
            if (weapons[i]) {
                int tmp = weapons[i]->Attack(pEnemy);
                if (tmp == 0) {                 // ②
                    delete weapons[i];
                    weapons[i] = NULL;
                    validAttack = true;
                }
                if (nStrength <= 0 || pEnemy->GetStrength() <= 0)
                    return 0;
                pEnemy->FightBack(this);        // ③
                if (nStrength <= 0 || pEnemy->GetStrength() <= 0)
                    return 0;
                if (tmps != pEnemy->GetStrength() || tmp != 1)
                    validAttack = true;         // ④
            }
        }
        if (!validAttack) break;               // ⑤
    }
    return 0;
}
```

在①处，每轮攻击前记录敌人当前的生命值 `tmps`，用于判断本轮是否发生了变化。

在②处，若 `Attack()` 返回 0，说明武器已消耗（arrow 用了两次或 bomb 爆炸），立即 `delete` 并将指针置 `NULL`。

在③处，攻击方每用一件武器，敌方立即用 `FightBack` 还击一次。

在④处，只要本轮有武器攻击、且敌人生命值发生了变化（或武器被消耗），就标记 `validAttack = true`，下一轮继续。

在⑤处，若整轮扫描所有武器都没有产生任何变化，说明双方陷入平局僵局，跳出循环。

### 3.4.6　`FightBack()`：被动还击

每次攻击方用完一件武器后，立即触发对方的 `FightBack()`——还击只用当前轮次的一件武器：

```cpp
// warcraft3.cpp
--snip--
void CWarrior::FightBack(CWarrior * pEnemy)
{
    if (weaponIdx == MAX_WPS) return;   // ①
    bool done = false;
    int i = weaponIdx;
    for (; i < MAX_WPS; ++i) {
        if (weapons[i]) {
            done = true;
            int tmp = weapons[i]->Attack(pEnemy);
            if (tmp == 0) { delete weapons[i]; weapons[i] = NULL; }
            break;
        }
    }
    if (done)
        weaponIdx = (i + 1) % MAX_WPS;   // ②
    else {
        weaponIdx = 0;
        // 从头再找一遍，若仍无武器则 weaponIdx = MAX_WPS 标记用尽
        ...
    }
}
```

在①处，`weaponIdx == MAX_WPS` 是特殊标记，表示武器已全部耗尽，直接返回不再还击。

在②处，`FightBack` 每次只用当前轮次的一件武器，用完后 `weaponIdx` 移到下一格，下次还击从这里继续——这实现了"双方交替使用武器"的规则。

### 3.4.7　缴获武器：`TakeEnemyWeapons()`——wolf 分支

`TakeEnemyWeapons()` 处理两种场景：wolf 在战前抢武器，以及战后胜方缴获。先来看函数的开头和 wolf 分支：

```cpp
// warcraft3.cpp
--snip--
string CWarrior::TakeEnemyWeapons(CWarrior * pEnemy, bool beforeFight)
{
    SortWeapons();
    int i;
    for (i = 0; i < MAX_WPS; ++i)
        if (weapons[i] == NULL) break;   // ①
    if (i == MAX_WPS) return "";          // ②

    string retVal = "";
    if (beforeFight) {   // ③  wolf 抢武器
        int nKindNo = -1;
        int wolfget = 0;
        for (int k = 0; i < MAX_WPS && k < MAX_WPS; ++k) {
            if (pEnemy->weapons[k]) {
                if (nKindNo == -1 ||
                    pEnemy->weapons[k]->nKindNo == nKindNo) {
                    nKindNo = pEnemy->weapons[k]->nKindNo;
                    weapons[i++] = pEnemy->weapons[k];
                    pEnemy->weapons[k]->master = this;   // ④
                    pEnemy->weapons[k] = NULL;
                    ++wolfget;
                } else break;
            }
        }
        if (wolfget > 0) {
            char tmp[100];
            sprintf(tmp, "%d %s", wolfget, CWeapon::Names[nKindNo]);
            retVal = tmp;
        }
    }
    --snip--
```

在①处，先在自己的武器数组里找第一个空槽 `i`。

在②处，若已经满了（10 件），直接放弃缴获，不会超出上限。

在③处，`beforeFight = true` 代表 wolf 抢武器：只抢敌人编号**最小的那种**武器，若有多件则全抢，但不超过自己的 10 件上限。

在④处，把武器的 `master` 指针改指向新的拥有者——否则武器的 `GetForce()` 还会按照原主人的攻击力计算。

### 3.4.8　缴获武器：`TakeEnemyWeapons()`——战后分支（接上一小节）

接上一小节，补上战斗结束后胜方统一缴获的逻辑：

```cpp
// warcraft3.cpp（接上）
    --snip--
    } else {   // ①  战斗结束后缴获
        pEnemy->SortWeapons(true);
        for (int k = 0; i < MAX_WPS && k < MAX_WPS; ++k) {
            if (pEnemy->weapons[k]) {
                weapons[i++] = pEnemy->weapons[k];
                pEnemy->weapons[k]->master = this;
                pEnemy->weapons[k] = NULL;
            }
        }
    }
    SortWeapons();
    return retVal;
}
```

在①处，普通胜方缴获时使用 `WpCompare2` 排序（优先缴获没用过的箭），再将所有能放下的武器一并取走。最后调用 `SortWeapons()` 整理自己的武器数组，使后续战斗时武器顺序正确。

## 3.5　各武士子类的特殊行为

### 3.5.1　`CLion`：忠诚度与逃跑

`CLion` 覆盖了 `Runaway()` 和 `March()`，实现忠诚度机制：

```cpp
// warcraft3.cpp
--snip--
class CLion : public CWarrior
{
    int nLoyalty;
public:
    static int nLoyaltyDec;
    CLion(int nId_, int nStrength_, int nForce_,
          int nCityNo_, CHeadquarter * pHeadquarter_) :
        CWarrior(nId_, nStrength_, nForce_, nCityNo_, pHeadquarter_)
    {
        nLoyalty = pHeadquarter->nMoney;   // ①
        weapons[0] = CWeapon::NewWeapon(nId_ % 3, this);
    }
    virtual bool Runaway() { return nLoyalty <= 0; }   // ②
    virtual void March() {
        CWarrior::March();
        nLoyalty -= CLion::nLoyaltyDec;   // ③
    }
};
```

在①处，lion 的初始忠诚度等于它降生时司令部剩余的生命元数目（已扣减过造它的费用后）。

在②处，`Runaway()` 只需判断忠诚度是否降至 0 或以下，返回 `true` 时 `LionRunaway()` 方法会把它从列表中删除。

在③处，每次 `March()` 先调用基类移动，再减少忠诚度 `K`。`nLoyaltyDec` 是从主函数读入的 K 值，存为静态成员。

### 3.5.2　`CIceman`：行军损耗

`CIceman` 只覆盖 `March()`，每步损失当前生命值的 10%：

```cpp
// warcraft3.cpp
--snip--
void CIceman::March()
{
    CWarrior::March();
    int dec = nStrength / 10;   // ①
    nStrength -= dec;
}
```

在①处，损失量是当前生命值整除 10（去尾取整），再从 `nStrength` 里减去。注意先算 `dec` 再减，避免用减后的值计算。

### 3.5.3　`CDragon`：战后欢呼

`CDragon` 覆盖 `Yell()`，在战斗后若仍存活就发出欢呼：

```cpp
// warcraft3.cpp
--snip--
virtual string Yell() {
    if (nStrength > 0)   // ①
        return GetName() + " yelled in city " + MyIntToStr(nCityNo);
    else
        return "";
}
```

在①处，`nStrength > 0` 说明 dragon 在这场战斗中没有死亡，此时返回欢呼字符串；若已死亡（生命值 ≤ 0），则返回空字符串，调用方不会产生任何输出。`WarriorsAttack()` 在战斗结束后调用每个武士的 `Yell()`，只有返回非空字符串才添加事件。

## 3.6　`CHeadquarter` 的战场管理

### 3.6.1　用 `list` 管理武士

本章的 `CHeadquarter` 把武士从数组改为 `list<CWarrior*>`：

```cpp
// warcraft3.cpp
--snip--
class CHeadquarter {
    friend class CWarrior;
private:
    int nMoney;
    int nWarriorNo;
    list<CWarrior*> lstWarrior;   // ①
    int nColor;
    CKingdom * pKingdom;
    int nCityNo;
    CHeadquarter * pEnemyheadquarter;
public:
    static int MakingSeq[2][WARRIOR_NUM];
    --snip--
};
```

在①处，`list` 相对于数组的优势在于可以在遍历过程中**安全地删除当前元素**：`lstWarrior.erase(i)` 返回下一个有效迭代器，不会导致后续迭代器失效。lion 逃跑、武士死亡后的清理都依赖这一特性。

### 3.6.2　`LionRunaway()`

每小时第 5 分，检查并清除忠诚度不足的 lion：

```cpp
// warcraft3.cpp
--snip--
void CHeadquarter::LionRunaway()
{
    list<CWarrior*>::iterator i = lstWarrior.begin();
    while (i != lstWarrior.end()) {
        if ((*i)->Runaway()) {
            int nCityNo = (*i)->GetPosition();
            if (nColor == COLOR_RED && nCityNo == pKingdom->nCityNum + 1 ||
                nColor == COLOR_BLUE && nCityNo == 0)   // ①
            { i++; continue; }
            string s = (*i)->GetName() + " ran away";
            AddEvent(EVENT_LION_RUN, (*i)->nCityNo, nColor, s);
            i = lstWarrior.erase(i);   // ②
            continue;
        }
        i++;
    }
}
```

在①处，已经抵达敌方司令部的 lion 不会逃跑——它已经完成任务。

在②处，`erase(i)` 删除当前元素并返回下一个迭代器，直接用于继续循环，不会跳过或重复处理元素。

### 3.6.3　`WarriorsMarch()`

每小时第 10 分，所有武士向敌方方向前进一步：

```cpp
// warcraft3.cpp
--snip--
void CHeadquarter::WarriorsMarch(int nEnemyHeadquterCityNo)
{
    list<CWarrior*>::iterator i;
    for (i = lstWarrior.begin(); i != lstWarrior.end(); i++) {
        int nOldPos = (*i)->nCityNo;
        if (nColor == COLOR_RED) {
            if ((*i)->nCityNo < nEnemyHeadquterCityNo) (*i)->March();
        } else {
            if ((*i)->nCityNo > nEnemyHeadquterCityNo) (*i)->March();
        }
        char szTmp[100];
        sprintf(szTmp, " with %d elements and force %d",
                (*i)->nStrength, (*i)->nForce);
        if (nOldPos != nEnemyHeadquterCityNo) {
            if ((*i)->nCityNo == nEnemyHeadquterCityNo) {   // ①
                string s = (*i)->GetName() + " reached " +
                           pEnemyheadquarter->GetColorStr() +
                           " headquarter" + szTmp;
                AddEvent(EVENT_REACH, (*i)->nCityNo, nColor, s);
                pEnemyheadquarter->EnemyReach();              // ②
            } else {
                string s = (*i)->GetName() + " marched to city " +
                           MyIntToStr((*i)->GetPosition()) + szTmp;
                AddEvent(EVENT_MARCH, (*i)->GetPosition(), nColor, s);
            }
        }
    }
}
```

在①处，若武士在这一步刚好到达敌方司令部城市，就输出"reached ... headquarter"，而不是"marched to city"。

在②处，调用 `pEnemyheadquarter->EnemyReach()`，记录司令部被占领事件并通知 `CKingdom` 战争结束。

### 3.6.4　`WolfsRob()`

每小时第 35 分，所有 wolf 提前抢夺同城敌人的武器：

```cpp
// warcraft3.cpp
--snip--
void CHeadquarter::WolfsRob()
{
    list<CWarrior*>::iterator i = lstWarrior.begin();
    for (; i != lstWarrior.end(); i++) {
        if ((*i)->nStrength <= 0) continue;
        if ((*i)->GetName().find("wolf") == string::npos) continue;   // ①
        int nCityNo = (*i)->GetPosition();
        CWarrior * p = pEnemyheadquarter->QueryCityWarrior(nCityNo);
        if (p) {
            if (p->GetName().find("wolf") != string::npos) continue;  // ②
            string taken = (*i)->TakeEnemyWeapons(p, true);
            if (taken != "") {
                char szTmp[200];
                sprintf(szTmp, "%s took %s from %s in city %d",
                        (*i)->GetName().c_str(), taken.c_str(),
                        p->GetName().c_str(), nCityNo);
                AddEvent(EVENT_WOLFSROB, nCityNo, GetColor(), szTmp);
            }
        }
    }
}
```

在①处，跳过所有非 wolf 武士——只有 wolf 会抢武器。

在②处，若同城敌人也是 wolf，则双方都不抢（wolf 不抢 wolf）。`TakeEnemyWeapons(p, true)` 以 `beforeFight = true` 调用，返回描述字符串（如 `"3 bomb"`），若返回非空则记录事件。

### 3.6.5　进攻时机：确定先后手

每小时第 40 分是战斗时刻，奇数城市红方先攻，偶数城市蓝方先攻。下面先来看如何确定当前城市由谁先攻，以及如何发起攻击：

```cpp
// warcraft3.cpp
--snip--
void CHeadquarter::WarriorsAttack()
{
    list<CWarrior*>::iterator j = lstWarrior.begin();
    for (; j != lstWarrior.end(); j++) {
        CWarrior * pAttacker = (*j);
        if (pAttacker->nStrength <= 0) continue;
        int nCityNo = pAttacker->GetPosition();
        CWarrior * p = pEnemyheadquarter->QueryCityWarrior(nCityNo);
        if (p) {
            bool bShouldAttack = false;
            if (nColor == COLOR_RED && nCityNo % 2 == 1) bShouldAttack = true;   // ①
            if (nColor == COLOR_BLUE && nCityNo % 2 == 0) bShouldAttack = true;
            if (bShouldAttack) {
                pAttacker->Attack(p);   // ②
                p->Attack(pAttacker);
                --snip--
```

在①处，红方的 `WarriorsAttack()` 只处理奇数城市（红方先攻），蓝方的只处理偶数城市（蓝方先攻）。这样红蓝各自调用一次，每座城市恰好被处理一次。

在②处，`bShouldAttack` 为真时，先攻方调用 `Attack()` 主动出击，后攻方也立即调用 `Attack()` 反击；战斗的所有细节都封装在 `Attack()` 里，`WarriorsAttack()` 只负责触发。

### 3.6.6　先攻方死亡的处理（接上一小节）

接上一小节，战斗结束后先处理先攻方死亡的情况：

```cpp
// warcraft3.cpp（接上）
                --snip--
                char szTmp[200];
                if (pAttacker->nStrength <= 0) {
                    if (p->GetStrength() <= 0) {       // ①
                        if (pAttacker->GetColor() == COLOR_RED)
                            sprintf(szTmp, "both %s and %s died in city %d",
                                    pAttacker->GetName().c_str(),
                                    p->GetName().c_str(), nCityNo);
                        else
                            sprintf(szTmp, "both %s and %s died in city %d",
                                    p->GetName().c_str(),
                                    pAttacker->GetName().c_str(), nCityNo);
                    } else {   // ②
                        sprintf(szTmp, "%s killed %s in city %d remaining %d elements",
                                p->GetName().c_str(),
                                pAttacker->GetName().c_str(),
                                nCityNo, p->GetStrength());
                        p->TakeEnemyWeapons(pAttacker);
                    }
                }
                --snip--
```

在①处，先攻方与后攻方同时死亡，输出"both ... died"。红方名字在前、蓝方在后，因此需要根据 `pAttacker` 的颜色决定打印顺序。

在②处，先攻方死亡而后攻方存活，后攻方杀死先攻方，输出"killed"并缴获武器。

### 3.6.7　后攻方死亡与双方存活的处理（接上一小节）

接上一小节，处理剩余两种结局，随后记录事件并触发欢呼：

```cpp
// warcraft3.cpp（接上）
                --snip--
                } else if (p->GetStrength() <= 0) {   // ①
                    sprintf(szTmp, "%s killed %s in city %d remaining %d elements",
                            pAttacker->GetName().c_str(),
                            p->GetName().c_str(),
                            nCityNo, pAttacker->GetStrength());
                    pAttacker->TakeEnemyWeapons(p);
                } else {   // ②
                    if (pAttacker->GetColor() == COLOR_RED)
                        sprintf(szTmp, "both %s and %s were alive in city %d",
                                pAttacker->GetName().c_str(),
                                p->GetName().c_str(), nCityNo);
                    else
                        sprintf(szTmp, "both %s and %s were alive in city %d",
                                p->GetName().c_str(),
                                pAttacker->GetName().c_str(), nCityNo);
                }
                AddEvent(EVENT_FIGHT_RESULT, nCityNo, GetColor(), szTmp);
                string s = pAttacker->Yell();
                if (s != "") AddEvent(EVENT_YELL, nCityNo, pAttacker->GetColor(), s);
                s = p->Yell();
                if (s != "") AddEvent(EVENT_YELL, nCityNo, p->GetColor(), s);   // ③
            }
        }
    }
}
```

在①处，后攻方死亡而先攻方存活，逻辑与上一节的②对称——先攻方杀死后攻方并缴获武器。

在②处，双方都活着，输出"were alive"。

在③处，战斗结束后依次检查双方的 `Yell()`，dragon 存活时会追加一条欢呼事件。

## 3.7　主函数

主函数读取输入参数，创建 `CKingdom`，运行模拟，输出结果：

```cpp
// warcraft3.cpp
--snip--
int main()
{
    int nCases;
    cin >> nCases;
    int nCaseNo = 1;
    while (nCases--) {
        int M, N, K, T;
        cin >> M >> N >> K >> T;              // ①
        CLion::nLoyaltyDec = K;
        for (int i = 0; i < WARRIOR_NUM; i++)
            cin >> CWarrior::InitialLifeValue[i];
        for (int i = 0; i < WARRIOR_NUM; i++)
            cin >> CWarrior::InitalForce[i];
        CKingdom MyKingdom(N, M);             // ②
        MyKingdom.Run(T);                     // ③
        cout << "Case " << nCaseNo++ << ":" << endl;
        MyKingdom.OutputResult();             // ④
    }
    return 0;
}
```

在①处，本章新增了三个参数：N（城市数量）、K（lion 每步忠诚度减少量）、T（模拟截止时间，单位为分钟）。

在②处，`CKingdom(N, M)` 在构造函数里完成两个司令部的初始化和互相绑定，调用方无需关心细节。

在③处，`Run(T)` 以分钟为步长推进，每分钟调用 `TimePass`，战争结束后立即停止。

在④处，`OutputResult()` 对 `vEvent` 排序后统一输出——所有事件积累到这一刻才真正打印，这就是事件驱动架构的核心价值：**先收集，后排序，再输出**。

如果此时编译并运行程序，对于样例输入

```
1
20 1 10 400
20 20 30 10 20
5 5 5 5 5
```

应该得到如下输出：

```
Case 1:
000:00 blue lion 1 born
Its loyalty is 10
000:10 blue lion 1 marched to city 1 with 10 elements and force 5
000:50 20 elements in red headquarter
000:50 10 elements in blue headquarter
000:55 blue lion 1 has 0 sword 1 bomb 0 arrow and 10 elements
001:05 blue lion 1 ran away
001:50 20 elements in red headquarter
001:50 10 elements in blue headquarter
...
```

红方一开始没有足够的生命元造出第一个武士（红方制造顺序首位是 iceman，初始生命值 30，但司令部只有 20），所以全程只有蓝方的 lion 降生、行军、报告后在第二小时因忠诚度降至 0 逃跑。
