# 第 1 章　代码清单

本文档收录第 1 章所有代码片段，按小节顺序排列，供对照阅读。

---

## 代码 1.2.1　Warrior 类声明

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

---

## 代码 1.2.2　Warrior 构造函数

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

---

## 代码 1.2.3　PrintResult()

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

---

## 代码 1.3.1　Headquarter 类声明

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

---

## 代码 1.3.2　Headquarter::Init()

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

---

## 代码 1.3.3　Headquarter 析构函数

```cpp
// warcraft1.cpp
--snip--
Headquarter::~Headquarter()
{
    for (int i = 0; i < totalWarriorNum; i++)
        delete pWarriors[i];   // ①
}
```

---

## 代码 1.4.1　Produce() 第一部分：跳过造不起的武士

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

---

## 代码 1.4.2　Produce() 第二部分：停产判断与正式生产

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

---

## 代码 1.5　GetColor() 与静态成员定义

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

---

## 代码 1.6　main()

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
