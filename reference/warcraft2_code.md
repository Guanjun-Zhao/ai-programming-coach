# 第 2 章　代码清单

本文档收录第 2 章所有代码片段，按小节顺序排列，供对照阅读。

---

## 代码 2.2　CWeapon 类声明

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

---

## 代码 2.3.1　CWarrior 类声明

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

---

## 代码 2.3.2　CWarrior 构造函数与 PrintResult(int, int)

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

---

## 代码 2.4.1　CDragon 类

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

---

## 代码 2.4.2　CNinja 类

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

---

## 代码 2.4.3a　CIceman 类

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

---

## 代码 2.4.3b　CLion 类

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

---

## 代码 2.4.3c　CWolf 类

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

---

## 代码 2.5　Produce() 中的 switch 工厂

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

---

## 代码 2.6a　GetColor()

```cpp
// warcraft2.cpp
--snip--
void CHeadquarter::GetColor(char* szColor)
{
    if (nColor == 0) strcpy(szColor, "red");
    else             strcpy(szColor, "blue");
}
```

---

## 代码 2.6b　静态成员定义

```cpp
// warcraft2.cpp
--snip--
const char* CWeapon::Names[WEAPON_NUM]     = {"sword", "bomb", "arrow"};
int         CWeapon::InitialForce[WEAPON_NUM];

const char* CWarrior::Names[WARRIOR_NUM]   = {"dragon","ninja","iceman","lion","wolf"};
int         CWarrior::InitialLifeValue[WARRIOR_NUM];
int         CHeadquarter::MakingSeq[2][WARRIOR_NUM] = { {2,3,4,1,0}, {3,0,1,2,4} };
```

---

## 代码 2.7　main()

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
