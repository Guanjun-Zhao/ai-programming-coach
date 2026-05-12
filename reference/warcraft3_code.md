# 第 3 章　代码清单

本文档收录第 3 章所有代码片段，按小节顺序排列，供对照阅读。

---

## 代码 3.2.1　EEventType 枚举与 CEvent 类

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
        nCityNo(nCityNo_), nColor(nColor_), sDescribe(s) {}

    void Output()
    {
        char szTime[20];
        sprintf(szTime, "%03d:%02d", nTime / 60, nTime % 60);   // ③
        cout << szTime << " " << sDescribe << endl;
    }
    bool operator<(const CEvent & e2) const {     // ④
        if (nTime != e2.nTime)   return nTime < e2.nTime;
        if (nCityNo != e2.nCityNo) return nCityNo < e2.nCityNo;
        if (eEventType != e2.eEventType) return eEventType < e2.eEventType;
        return nColor < e2.nColor;
    }
};
```

---

## 代码 3.2.2a　CKingdom 类声明

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
    CKingdom(int nCityNum_, int nInitMoney) :
        nTimeInMinutes(0),
        Red(COLOR_RED, nInitMoney, 0),
        Blue(COLOR_BLUE, nInitMoney, nCityNum_ + 1),   // ③
        nCityNum(nCityNum_)
    {
        Red.SetKingdom(this);   Red.SetEnemy(&Blue);
        Blue.SetKingdom(this);  Blue.SetEnemy(&Red);
        nEndTime = 3000000;
    }
    void Run(int T) {
        for (int t = 0; t <= T; t++)
            if (TimePass(t) == 0) return;   // ④
    }
    int TimePass(int nMinutes);    // ⑤
    void OutputResult() {
        sort(vEvent.begin(), vEvent.end());   // ⑥
        for (int i = 0; i < vEvent.size(); i++)
            vEvent[i].Output();
    }
    void AddEvent(EEventType eType, int nCityNo,
                  int nColor, const string & s) {
        CEvent tmp(eType, nTimeInMinutes, nCityNo, nColor, s);
        vEvent.push_back(tmp);
    }
    void WarEnd() {
        if (nEndTime == 3000000) nEndTime = nTimeInMinutes;   // ⑦
    }
};
```

---

## 代码 3.2.2b　CKingdom::TimePass()

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

---

## 代码 3.3.1　CWeapon 基类

```cpp
// warcraft3.cpp
--snip--
class CWeapon
{
public:
    int nKindNo;
    CWarrior * master;                              // ①
    static const char * Names[WEAPON_NUM];

    virtual int GetForce() = 0;                     // ②
    virtual int Attack(CWarrior * pEnemy);          // ③
    static CWeapon * NewWeapon(int idx, CWarrior * master);  // ④
    CWeapon(CWarrior * m) : master(m) {}
};

int CWeapon::Attack(CWarrior * pEnemy) {
    pEnemy->Hurted(GetForce());
    return 1;    // ⑤
}
```

---

## 代码 3.3.2a　CSWord、CArrow、CBomb 子类

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

class CArrow : public CWeapon
{
    int usedTimes;
public:
    virtual int GetForce() {
        return master->GetForce() * 3 / 10;   // ②
    }
    CArrow(CWarrior * master) : CWeapon(master), usedTimes(0) { nKindNo = 2; }
    virtual int Attack(CWarrior * pEnemy) {
        CWeapon::Attack(pEnemy);
        ++usedTimes;
        if (usedTimes == 2) return 0;   // ③
        return 2;
    }
};

class CBomb : public CWeapon
{
public:
    virtual int GetForce() {
        return master->GetForce() * 4 / 10;   // ④
    }
    CBomb(CWarrior * master) : CWeapon(master) { nKindNo = 1; }
    virtual int Attack(CWarrior * pEnemy) {
        int force = GetForce();
        if (master->GetName().find("ninja") == string::npos)
            master->Hurted(force / 2);   // ⑤
        pEnemy->Hurted(force);
        return 0;   // ⑥
    }
};
```

---

## 代码 3.3.2b　CWeapon::NewWeapon() 工厂方法

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

---

## 代码 3.4.1　CWarrior 新字段与 March()

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
             CHeadquarter * pHeadquarter_) :
        nId(nId_), nStrength(nStrength_), nForce(nForce_),
        nCityNo(nCityNo_), pHeadquarter(pHeadquarter_), weaponIdx(0)
    {
        memset(weapons, 0, sizeof(weapons));   // ⑤
    }
    virtual ~CWarrior() {
        for (int i = 0; i < MAX_WPS; ++i)
            if (weapons[i]) delete weapons[i];
    }
    virtual string GetName() = 0;
    virtual void March();
    void SortWeapons(bool forTaken = false);
};

void CWarrior::March()
{
    if (GetColor() == COLOR_RED) nCityNo++;   // ⑥
    else                          nCityNo--;
    weaponIdx = 0;   // ⑦
}
```

---

## 代码 3.4.2　WpCompare() 与 SortWeapons()

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

---

## 代码 3.4.3　Attack() 与 FightBack()

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

void CWarrior::FightBack(CWarrior * pEnemy)
{
    if (weaponIdx == MAX_WPS) return;   // ⑥
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
        weaponIdx = (i + 1) % MAX_WPS;   // ⑦
    else {
        weaponIdx = 0;
        // 从头再找一遍，若仍无武器则 weaponIdx = MAX_WPS 标记用尽
        ...
    }
}
```

---

## 代码 3.4.4　TakeEnemyWeapons()

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
    } else {   // ⑤  战斗结束后缴获
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

---

## 代码 3.5.1　CLion：忠诚度与逃跑

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

---

## 代码 3.5.2　CIceman::March()

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

---

## 代码 3.5.3　CDragon::Yell()

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

---

## 代码 3.6.1　CHeadquarter 类声明（list 容器）

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

---

## 代码 3.6.2　LionRunaway()

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

---

## 代码 3.6.3　WarriorsMarch()

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

---

## 代码 3.6.4　WolfsRob()

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

---

## 代码 3.6.5　WarriorsAttack()

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
                char szTmp[200];
                if (pAttacker->nStrength <= 0) {
                    if (p->GetStrength() <= 0) {
                        // 双方都死：红武士写前面
                        sprintf(szTmp, "both %s and %s died in city %d", ...);
                    } else {   // ③
                        sprintf(szTmp, "%s killed %s in city %d remaining %d elements", ...);
                        p->TakeEnemyWeapons(pAttacker);
                    }
                } else if (p->GetStrength() <= 0) {   // ④
                    sprintf(szTmp, "%s killed %s in city %d remaining %d elements", ...);
                    pAttacker->TakeEnemyWeapons(p);
                } else {   // ⑤
                    sprintf(szTmp, "both %s and %s were alive in city %d", ...);
                }
                AddEvent(EVENT_FIGHT_RESULT, nCityNo, GetColor(), szTmp);
                string s = pAttacker->Yell();
                if (s != "") AddEvent(EVENT_YELL, nCityNo, pAttacker->GetColor(), s);
                s = p->Yell();
                if (s != "") AddEvent(EVENT_YELL, nCityNo, p->GetColor(), s);   // ⑥
            }
        }
    }
}
```

---

## 代码 3.7　main()

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
