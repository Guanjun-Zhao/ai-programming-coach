//数据里面没有出现狼由于达到武器数目限制而无法全部抢走的情况 
#include <iostream>
#include <vector>
#include <list>
#include <string>
#include <algorithm>
#include <cstring>
#include <cstdlib>
#include <cstdio>
#include <cmath>
#include <iomanip>
const double EPS = 1e-6;
using namespace std;
enum EEventType { EVENT_BORN, EVENT_LION_RUN,EVENT_MARCH, EVENT_WOLFSROB, EVENT_FIGHT_RESULT,EVENT_YELL, EVENT_EARNMONEY,
				  EVENT_REACH,EVENT_CITYTAKEN,EVENT_PRINTMONEY,EVENT_WARRIOR_REPORT };
enum { WEAPON_SWORD,WEAPON_BOMB,WEAPON_ARROW };
enum { DRAGON,NINJA,ICEMAN,LION,WOLF};

#define WEAPON_NUM 3
#define WARRIOR_NUM 5

class CHeadquarter;
class CKingdom;
class CWarrior;
class CWeapon;

class CWeapon
{
	public:
		int nKindNo;
		friend class CWarrior;
		CWarrior * master;
		static const char * Names[WEAPON_NUM];
		friend int WpCompare(const void *wp1, const void * wp2);
		friend int WpCompare2(const void *wp1, const void * wp2);		

		virtual int GetForce() { };
		virtual int Attack(CWarrior * pEnemy) ; // 0 打没了  1 没变化 2 有变化 
		static CWeapon * NewWeapon(int idx,CWarrior * master) ;
		CWeapon(CWarrior * m):master(m) { }

};



#define COLOR_RED 0
#define COLOR_BLUE 1
#define COLOR_NONE 3

typedef  CWarrior* PWARRIOR;
string MyIntToStr( int n)
{
	char szTmp[300];
	sprintf(szTmp,"%d",n);
	return szTmp;
}
//cls CWarrior
class CWarrior
{
public:
	static const int MAX_WPS = 10; 
	
friend class CHeadquarter;
protected:
	int nStrength;
	int nForce;
	int nCityNo;
	int nId;
	int weaponIdx; //当前轮到哪件武器攻击 
	CHeadquarter * pHeadquarter;
	CWeapon * weapons[MAX_WPS];
public:

	static const char * Names[WARRIOR_NUM];
	static int InitialLifeValue [WARRIOR_NUM];
	static int InitalForce [WARRIOR_NUM];	
	virtual bool Runaway() { return false; }
	virtual string Yell() { return ""; }

	virtual string TakeEnemyWeapons( CWarrior * pEnemy,bool beforeFight = false);
	virtual void Hurted(int force) { nStrength -= force; }
	virtual ~CWarrior() { 
		for(int i = 0;i <MAX_WPS; ++i)
			if( weapons[i])
				delete weapons[i];
	}
    virtual int Attack( CWarrior * pEnemy);
 	virtual void FightBack( CWarrior * pEnemy);
	virtual string GetName() = 0;
	virtual void March();

	string GetColorStr();
	int GetColor() const;
	CWarrior(int nId_,int nStrength_,int nForce_,int nCityNo_, CHeadquarter * pHeadquarter_):
		nId(nId_),nStrength(nStrength_),nForce(nForce_),nCityNo(nCityNo_),pHeadquarter(pHeadquarter_),weaponIdx(0)
	{
		memset(weapons,0,sizeof(weapons)); 
	}
	int GetStrength( )	{		return nStrength;	}
	int GetForce()	{		return nForce;	}
	void SetStrength(int n)	{	nStrength = n;	}
	void SetForce(int n)	{		nForce = n;	}
	int GetPosition() 	{		return nCityNo;	}
	string ReportStatus()
	{
		int swords = 0;
		int bombs = 0;
		int arrows = 0;
		for(int i = 0;i <MAX_WPS; ++i) {
			if( weapons[i]) {
				if( weapons[i]->nKindNo == 0)
					++swords ;
				else if (weapons[i]->nKindNo == 1)
					++bombs;
				else
					++arrows;
			}
		}
		char tmp[100];
		sprintf(tmp," has %d sword %d bomb %d arrow and %d elements",swords,bombs,arrows,nStrength);
		return tmp; 
	}
    void SortWeapons(bool forTaken = false);
};

class CNinja:public CWarrior
{
friend class CHeadquarter;
public:
	//CNinja constructor
	CNinja(int nId_,int nStrength_,int nForce_,int nCityNo_, CHeadquarter * pHeadquarter_):
		CWarrior(nId_,nStrength_,nForce_,nCityNo_,pHeadquarter_)
	{
		int wp1 = nId % 3;
		int wp2 = (nId + 1) % 3;
		weapons[0] = CWeapon::NewWeapon(nId % 3,this);
		weapons[1] = CWeapon::NewWeapon((nId + 1) % 3,this);
		SortWeapons();		
	}
	virtual string GetName();

};
class CDragon:public CWarrior
{
friend class CHeadquarter;
public:
//CDragon Constructor
	CDragon(int nId_,int nStrength_,int nForce_,int nCityNo_, CHeadquarter * pHeadquarter_):
	CWarrior(nId_,nStrength_,nForce_,nCityNo_,pHeadquarter_){
		weapons[0] = CWeapon::NewWeapon(nId % 3,this);	
	}
    virtual int Attack( CWarrior * p) ;
	virtual string GetName();
	virtual string Yell() {
		if( nStrength > 0) { //没有战死
			return GetName() + " yelled in city " + MyIntToStr(nCityNo);
		}
		else
			return "";
	}	
	
};

class CLion:public CWarrior
{
	friend class CHeadquarter;
private:
	int nLoyalty;
public:
	static int nLoyaltyDec;
	//CLion Constructor
	CLion(int nId_,int nStrength_,int nForce_,int nCityNo_, CHeadquarter * pHeadquarter_);
	virtual string GetName();
	bool Runaway ()	{	
		return nLoyalty <= 0; 
	}
	virtual void March();
};


class CIceman:public CWarrior
{
friend class CHeadquarter;
public:
	//CIceman constructor	
	CIceman(int nId_,int nStrength_,int nForce_,int nCityNo_, CHeadquarter * pHeadquarter_):
		CWarrior(nId_,nStrength_,nForce_,nCityNo_,pHeadquarter_)
	{
		weapons[0] = CWeapon::NewWeapon(nId % 3,this);		
	}
	virtual void March() ;
	virtual string GetName() ;
};

class CWolf:public CWarrior
{
friend class CHeadquarter;
public:
	//CWolf Constructor
	CWolf(int nId_,int nStrength_,int nForce_,int nCityNo_, CHeadquarter * pHeadquarter_):
		CWarrior(nId_,nStrength_,nForce_,nCityNo_,pHeadquarter_)
	{
	}
	virtual string GetName() ;
};
class CSWord : public CWeapon
{
public:
	virtual int GetForce() {
		return master->GetForce() * 2 / 10;
	}
	CSWord(CWarrior * m):CWeapon(m) { nKindNo = 0; }
};
class CArrow : public CWeapon
{
	int usedTimes ;
	public:
	virtual int GetForce() {
		return master->GetForce() * 3 / 10;
		
//		return int(master->GetForce() * 0.3); //这个可以 
/*这个可以 
		int n = int(master->GetForce() * 0.3);
		return n;
*/
		
/*这个不行 
		double f1 = master->GetForce() * 0.3;  
		return f1;
结论：编译器会考察，把		master->GetForce() * 0.3;   转int的时候，编译器看到
乘出来结果是 4.99999999 就转成5 但是如果将这个结果赋值给 f,然后再转 那因为 f是4.9999，就直接去尾了。 
 
*/
		
//*/		
/*这个不行 
		double f1 = master->GetForce() * 0.3;
		int f2 = (int)f1;
		return f2;
*/		
/*
		++ f2;
		if( fabs(f2 - f1) < EPS )
			return f2;
		return f1;
*/		
	}
	CArrow(CWarrior * master):CWeapon(master),usedTimes(0)  { 
		nKindNo = 2; 
	}
	virtual int Attack(CWarrior * pEnemy) {	
		CWeapon::Attack(pEnemy);
		++ usedTimes;
		if( usedTimes == 2)
			return 0;
		return 2;
	}	
	friend int WpCompare(const void *wp1, const void * wp2);	
	friend int WpCompare2(const void *wp1, const void * wp2);		
};
class CBomb : public CWeapon
{
	public:
	CBomb(CWarrior * master):CWeapon(master) { 
		nKindNo = 1; 
	}

	virtual int GetForce() {
		return master->GetForce() * 4 / 10;
	}
	virtual int Attack(CWarrior * pEnemy) {	
		int force = GetForce();
		if (master->GetName().find("ninja") == string::npos )
			master->Hurted(force/2);		
		pEnemy->Hurted(force);
		return 0;
	}	
};
CWeapon * CWeapon::NewWeapon(int idx,CWarrior * master)
{
		switch(idx) {
			case 0:
				return new CSWord(master);
			case 1:
				return new CBomb(master);				
			case 2:
				return new CArrow(master);				
		}
		return NULL;
	
}
int WpCompare(const void *wp1, const void * wp2)
{
	CWeapon ** p1 = (CWeapon ** ) wp1;
	CWeapon ** p2 = (CWeapon ** ) wp2;	
	if( *p1 == NULL )
		return 1;
	if( *p2 == NULL )
		return -1;
	if( (*p1)->nKindNo != (*p2)->nKindNo )
		return (*p1)->nKindNo - (*p2)->nKindNo;
	else {
		if( (*p1)->nKindNo == WEAPON_ARROW )  // arrow
			return ((CArrow *)(*p2))->usedTimes - ((CArrow *)(*p1))->usedTimes;
		else 
			return 0;
	}
}
int WpCompare2(const void *wp1, const void * wp2)
{
	CWeapon ** p1 = (CWeapon ** ) wp1;
	CWeapon ** p2 = (CWeapon ** ) wp2;	
	if( *p1 == NULL )
		return 1;
	if( *p2 == NULL )
		return -1;
	if( (*p1)->nKindNo != (*p2)->nKindNo )
		return (*p1)->nKindNo - (*p2)->nKindNo;
	else {
		if( (*p1)->nKindNo == WEAPON_ARROW )  // arrow
			return ((CArrow *)(*p1))->usedTimes - ((CArrow *)(*p2))->usedTimes;
		else
			return 0;
	}
}

//cls CHeadQuarter
class CHeadquarter {

friend class CWarrior;
friend class CWolf;
friend class CDragon;
friend class CIceman;
friend class CLion;
friend class CNinja;
private:
	int nBloodMoney ; //addfor 2010 纪录打仗赢后得到的
	int nMoney;
	int nWarriorNo;
	list<CWarrior * > lstWarrior;
	int nColor;
	CKingdom * pKingdom;
	int nCityNo; //red: 0 ,blue nCitynum + 1
	CHeadquarter * pEnemyheadquarter;
	vector<CWarrior *> vAwardList;
public:
	static int MakingSeq[2][WARRIOR_NUM];
	CHeadquarter(int nColor_, int nMoney_,int nCityNo_ ) : nColor(nColor_), nWarriorNo(1),
			    nMoney(nMoney_),nCityNo(nCityNo_),nBloodMoney(0)
	{
	}
	~CHeadquarter()
	{
		list<CWarrior*> ::iterator p;
		for( p = lstWarrior.begin(); p != lstWarrior.end(); p ++ )
			delete (* p);
		lstWarrior.clear();
	}
	void SetEnemy( CHeadquarter * p)
	{
		pEnemyheadquarter = p;
	}
	void SetKingdom( CKingdom * p)
	{
		pKingdom = p;
	}
	void AddEvent( EEventType eType, int nCityNo, int nColor,const string & sEventString);
	void PrintMoney();
	string GetColorStr() 
	{
		if( nColor == COLOR_RED)
			return "red";
		else
			return "blue";
	}
	int GetColor()
	{
		return nColor;
	}
	void LionRunaway();
	void Bomb();
	void WarriorBorn();
	void WarriorsMarch(int nEnemyHeadquterCityNo );
	void WarriorsAttack();
	void WolfsRob();
	void WarriorsReport();
	void EnemyReach();
	CWarrior * QueryCityWarrior( int nCityNo);
	
};

	//CLion Constructor
CLion::CLion(int nId_,int nStrength_,int nForce_,int nCityNo_, CHeadquarter * pHeadquarter_):
		CWarrior(nId_,nStrength_,nForce_,nCityNo_,pHeadquarter_)	{
		nLoyalty = pHeadquarter ->nMoney;
		weapons[0] = CWeapon::NewWeapon(nId % 3,this);			
}


class CEvent
{
private:
	EEventType eEventType;
	int nTime;
	int nCityNo;
	int nColor;
	string sDescribe;
public:	
	  CEvent(EEventType eEventType_,int nTime_,int nCityNo_,int nColor_, const string & s) :
		eEventType(eEventType_),nTime(nTime_),nCityNo(nCityNo_),nColor(nColor_),sDescribe(s) 
	  {
	  }
	  void Output()  
	  {
		char szTime[20];
		sprintf(szTime,"%03d:%02d",nTime /60, nTime % 60);
		cout << szTime << " " << sDescribe << endl;
	  }
	  bool operator < ( const CEvent & e2 ) const {
		if( nTime < e2.nTime )
			return true;
		else if( nTime > e2.nTime )
			return false;
/*
		if( eEventType == e2.eEventType && eEventType == EVENT_WARRIOR_REPORT) {
			if( nColor < e2.nColor )
				return true;
			else if( nColor == e2.nColor) 
				return nCityNo < e2.nCityNo ;
			else
				return false;
		}
*/
		if( nCityNo < e2.nCityNo )
			return true;
		else if( nCityNo > e2.nCityNo )
			return false;
		
		if( eEventType < e2.eEventType )
			return true;
		else if( eEventType > e2.eEventType )
			return false;
		if( nColor < e2.nColor )
			return true;
		else
			return false;
	  }


};
class CKingdom 
{
	friend class CHeadquarter;
private:
	CHeadquarter Red, Blue;
	int nTimeInMinutes;
	vector<CEvent> vEvent;
	int nEndTime;
	int nCityNum;
public:
	void Run(int T) {
		for( int t = 0; t <= T; t ++ ) { //modifor 2010 old: t < T
			if( TimePass(t) == 0)
				return ;
		}
	}
	CKingdom(int nCityNum_,int nInitMoney):
		nTimeInMinutes(0),Red(COLOR_RED,nInitMoney,0),Blue(COLOR_BLUE,nInitMoney,nCityNum_ + 1),
			nCityNum(nCityNum_)
	{
		Red.SetKingdom(this);
		Red.SetEnemy( &Blue);
		Blue.SetKingdom(this);
		Blue.SetEnemy( &Red);
		nEndTime = 3000000;
	}
	int TimePass(int nMinutes) ;
	string SysemTimeStr() 
	{
		char szTime[20];
		sprintf(szTime,"%03d:%02d",nTimeInMinutes /60, nTimeInMinutes % 60);
		return szTime;
	}
	int GetTime()
	{
		return nTimeInMinutes;	
	}
	void WarEnd()
	{
		if( nEndTime == 3000000)
			nEndTime = nTimeInMinutes;
	}
	void OutputResult()
	{
		sort(vEvent.begin(),vEvent.end());
		for( int i = 0;i < vEvent.size();i ++ )
			vEvent[i].Output();
	}
	void AddEvent( EEventType eType, int nCityNo, int nColor, const string & sEventString);
};


//CWarrior functions
int CWarrior::GetColor() const
{
	return pHeadquarter->GetColor();
}
string CWarrior::GetColorStr()
{
	return pHeadquarter->GetColorStr();
}
void CWarrior::FightBack( CWarrior * pEnemy)
{
	if( weaponIdx == MAX_WPS)
		return;
	bool done = false;
	int i = weaponIdx;
	for( ;i < MAX_WPS; ++i) {
		if( weapons[i]) {
			done = true;
			int tmp =	weapons[i] ->Attack(pEnemy);
			if( tmp == 0) {
				delete  weapons[i];
				weapons[i]= NULL;
			}
			break;
		}
	}
	if(done) 
		weaponIdx = (i + 1 ) % MAX_WPS;
	else {
		weaponIdx = 0;
		int i = weaponIdx;
		for( ;i < MAX_WPS; ++i) {
			if( weapons[i]) {
				done = true;
				int tmp =	weapons[i] ->Attack(pEnemy);
				if( tmp == 0) {
					delete  weapons[i];
					weapons[i]= NULL;
				}
				break;
			}
		}
		if( done )
				weaponIdx = (i + 1 ) % MAX_WPS;
		else
			weaponIdx = MAX_WPS;
	}
}
int CWarrior::Attack( CWarrior * pEnemy)
{
	char szTmp[200];
	if( nStrength <= 0 || pEnemy->GetStrength() <= 0)
		return 0;
	while( true ) {
		bool validAttack = false;		
		for(int i = 0;i < MAX_WPS; ++i ) {
			int tmps = pEnemy->GetStrength();
			if( weapons[i] ) {
				
				int tmp = weapons[i]->Attack(pEnemy);
				if( tmp == 0) {
					delete weapons[i];
					weapons[i] = NULL;
					validAttack = true;
				}
				if( nStrength <= 0 || pEnemy->GetStrength() <= 0)
					return 0;
				pEnemy->FightBack(this);					
				if( nStrength <= 0 || pEnemy->GetStrength() <= 0)
					return 0;
				if( tmps != pEnemy->GetStrength() || tmp != 1) //tmp == 1表示武器没变化 
					validAttack = true;
			}
		}
		if (!validAttack)
			break;
	}
	return 0;
}

void CWarrior::March() 
{
	if( GetColor() == COLOR_RED)
		nCityNo ++;
	else
		nCityNo --;
	weaponIdx = 0;

}
void CWarrior::SortWeapons(bool forTaken)
{
	if(forTaken)
		qsort(weapons,MAX_WPS,sizeof(CWeapon *),WpCompare2);
	else
		qsort(weapons,MAX_WPS,sizeof(CWeapon *),WpCompare);
}
string CNinja::GetName()
{
	return pHeadquarter->GetColorStr() + " ninja " + MyIntToStr(nId);
}



int CDragon::Attack( CWarrior * p) 
{
	CWarrior::Attack(p);
	return 0;
}
string CDragon::GetName() 
{
	return pHeadquarter->GetColorStr() + " dragon " + MyIntToStr(nId); 
}
string CLion::GetName() 
{
	return pHeadquarter->GetColorStr() + " lion " + MyIntToStr(nId); 
}
void CIceman::March() 
{
	CWarrior::March();
	int dec = nStrength / 10;
	nStrength -= dec;
}
void CLion::March() 
{
	CWarrior::March();
	nLoyalty -= CLion::nLoyaltyDec;
}
string CIceman::GetName() 
{
	return pHeadquarter->GetColorStr() + " iceman " + MyIntToStr(nId); 
}

string CWarrior::TakeEnemyWeapons( CWarrior * pEnemy,bool beforeFight) 
{
	SortWeapons();
	int i;
	for (i = 0;i < MAX_WPS ; ++i)
		if( weapons[i] == NULL)
			break;
	if( i == MAX_WPS) {
		return "";
	}
	int wolfget = 0;			
	string retVal = "";
	if( beforeFight ) { //by wolf 
		int nKindNo = -1;
		for(int k = 0; i < MAX_WPS &&  k < MAX_WPS; ++k) {
			if( pEnemy->weapons[k] ) {
				if( nKindNo == -1 || pEnemy->weapons[k]->nKindNo == nKindNo) {
					nKindNo = pEnemy->weapons[k]->nKindNo;
					weapons[i++] = pEnemy->weapons[k];					
					pEnemy->weapons[k]->master  = this;					
					pEnemy->weapons[k] = NULL;					
					++ wolfget;
				}
				else 
					break;
			}
		}		
		
		if(wolfget > 0) {
			char tmp[100];
			sprintf(tmp,"%d %s",wolfget,CWeapon::Names[nKindNo]);
			retVal = tmp;
		}
	}
	else {
		pEnemy->SortWeapons(true);
		for(int k = 0; i < MAX_WPS && k < MAX_WPS; ++k) {
			if( pEnemy->weapons[k] ) {
				weapons[i++] = pEnemy->weapons[k];			
				pEnemy->weapons[k]->master  = this;
				pEnemy->weapons[k] = NULL;					
			}
		}			
	}
	SortWeapons();
	return retVal;
}
string CWolf::GetName() 
{
	return pHeadquarter->GetColorStr() + " wolf " + MyIntToStr(nId); 
}

//CHeadquarter functions

void CHeadquarter::LionRunaway()
{
	
	string sEventString;
	list<CWarrior * >::iterator i = lstWarrior.begin();
	while(i != lstWarrior.end() ) {
		if( (*i)->Runaway()) {
		//输出样例： 000:05 blue lion 1 ran away 
			int nCityNo = ( * i )->GetPosition();
			if( nColor == COLOR_RED &&  nCityNo == pKingdom->nCityNum + 1 ||
				nColor == COLOR_BLUE &&  nCityNo == 0 ) 
				continue;
			sEventString = (*i)->GetName() + " ran away";
			AddEvent( EVENT_LION_RUN, ( * i )-> nCityNo, nColor,sEventString); 
			i = lstWarrior.erase (i); //指向被erased的元素的后一个
			continue;
		}
		i ++;
	}
}
int CKingdom::TimePass(int nMinutes) {
	int i;
	nTimeInMinutes = nMinutes;
	if( nTimeInMinutes > nEndTime )
		return 0;
	int nRemain = nTimeInMinutes % 60;
	switch( nRemain) {
		case 0: //生产怪物
			Red.WarriorBorn();
			Blue.WarriorBorn();
			break;
		case 5: //lion可能逃跑
			Red.LionRunaway();
			Blue.LionRunaway();
			break;
		case 10: //前进
			Red.WarriorsMarch(nCityNum + 1);
			Blue.WarriorsMarch(0);
			break;
/*//addfor debug 
		case 25:
			Red.WarriorsReport();
			Blue.WarriorsReport();
			break;
//gwend */
			
		case 35: //wolf抢夺敌人武器 
			Red.WolfsRob();
			Blue.WolfsRob();
			break;
/*//addfor debug			
		case 38:
			Red.WarriorsReport();
			Blue.WarriorsReport();
			break;
//gwend			*/
		case 40://发生战斗
			Red.WarriorsAttack();
			Blue.WarriorsAttack();
			break;
		case 50:
			Red.PrintMoney(); //addfor 2010
			Blue.PrintMoney(); //addfor 2010
			break;
		case 55:
			Red.WarriorsReport();
			Blue.WarriorsReport();
	}
	return 1;
}
void CHeadquarter::EnemyReach()
{
	if( nColor == COLOR_RED ) 
		AddEvent( EVENT_CITYTAKEN, nCityNo,	nColor,string("red headquarter was taken"));
	else
		AddEvent( EVENT_CITYTAKEN, nCityNo, nColor,string("blue headquarter was taken"));
	pKingdom->WarEnd();
}

CWarrior * CHeadquarter::QueryCityWarrior( int nCityNo)
{
	list<CWarrior *>::iterator i;
	for( i = lstWarrior.begin();i != lstWarrior.end();i ++ ) {
		if( (* i )->GetPosition () == nCityNo)
			return ( * i );
	}
	return NULL;
}
void CHeadquarter::WarriorsMarch(int nEnemyHeadquterCityNo)
{
	list<CWarrior * >::iterator i;
	string sEventString;
	for( i = lstWarrior.begin();i != lstWarrior.end();i ++ ) {
		int nOldPos = ( * i ) ->nCityNo ;
		if( nColor == COLOR_RED ) {
			if( ( * i )-> nCityNo < nEnemyHeadquterCityNo)
				( *i )->March();
		}
		else {
			if( ( * i )-> nCityNo > nEnemyHeadquterCityNo)
				( *i )->March();
		}
		char szTmp[100];
		sprintf( szTmp," with %d elements and force %d",(*i)->nStrength,(*i)->nForce);
		
		

		if( nOldPos != nEnemyHeadquterCityNo) {
			if (( * i )-> nCityNo == nEnemyHeadquterCityNo ) {
				sEventString = (*i)->GetName() + " reached "+  pEnemyheadquarter->GetColorStr() + " headquarter" + szTmp;
				AddEvent( EVENT_REACH, ( * i )-> nCityNo, nColor,sEventString);
				pEnemyheadquarter->EnemyReach();
			}
			else {
				sEventString = (*i)->GetName() + " marched to city " + MyIntToStr(( * i )->GetPosition() ) + szTmp;
				AddEvent( EVENT_MARCH, ( * i )->GetPosition(), nColor,sEventString);
				//addfor debug
//				if( sEventString.find("blue lion 6 marched to city 10 with 10 elements and force 50")
//					!= string::npos)
//					cout << "UUUU" <<endl;
				//gwend
			}
		}
	}
}

void CHeadquarter::WarriorsReport()
{
	list<CWarrior * >::iterator i = lstWarrior.begin();
	string sEventString;
	while(i != lstWarrior.end()) {
		if( (*i)->nStrength <= 0) { //在35分，或刚才的战斗中已经被杀了
			i = lstWarrior.erase (i);
			continue;
		}
		string sEventString = (*i)->GetName();
		string sWeaponStatus = (*i)->ReportStatus();
		sEventString += sWeaponStatus;
		AddEvent( EVENT_WARRIOR_REPORT, ( * i )-> nCityNo, nColor,sEventString );
		i ++;
	}
}

void CHeadquarter::WarriorsAttack()
	{
	list<CWarrior * >::iterator j = lstWarrior.begin();
	for( j; j != lstWarrior.end();j ++) { //循环执行过程中有可能导致 lstWarrior中的某些元素被删，那么 这可能就有问题了 下面
		CWarrior * pAttacker = (*j); 
		//后面直接用 *j就老是莫名其妙的指针乱飞错，*(*j)的值变得不对，也不知道怎么回事 
		if( pAttacker->nStrength <= 0)
			continue;
		int nCityNo = pAttacker->GetPosition();
		CWarrior * p = pEnemyheadquarter->QueryCityWarrior(nCityNo);
		char szTmp[200];
		if( p ) { //eeee
			bool bShouldAttack = false;
			if( nColor == COLOR_RED && (nCityNo % 2 == 1))
				bShouldAttack = true;
			if( nColor == COLOR_BLUE && (nCityNo % 2 == 0))
				bShouldAttack = true;
			if( bShouldAttack ) {
				pAttacker->Attack (p);
				p->Attack (pAttacker);
				if( pAttacker->nStrength <= 0 ) {
					if( p->GetStrength() <= 0 ) {
						if( pAttacker->GetColor() == COLOR_RED )
							sprintf(szTmp,"both %s and %s died in city %d",
							pAttacker->GetName().c_str(), p->GetName().c_str(),nCityNo);
						else 
							sprintf(szTmp,"both %s and %s died in city %d",
							 p->GetName().c_str(),pAttacker->GetName().c_str(),nCityNo);
					}
//						000:40 both red iceman 1 and blue lion 12 died in city 2
					else {
					
//000:40 red iceman 1 killed blue lion 12 in city 2 remaining 20 elements 						
						sprintf(szTmp,"%s killed %s in city %d remaining %d elements",
							p->GetName().c_str(),pAttacker->GetName().c_str(),nCityNo, p->GetStrength());
						p->TakeEnemyWeapons(pAttacker);
					}
				}
				else if( p->GetStrength() <= 0 ) {
					sprintf(szTmp,"%s killed %s in city %d remaining %d elements",
							pAttacker->GetName().c_str(),p->GetName().c_str()
							,nCityNo, pAttacker->GetStrength());
					pAttacker->TakeEnemyWeapons(p);							
				}
				else {
					if(pAttacker->GetColor() == 	COLOR_RED )
//both red iceman 1 and blue lion 12 were alive in city 2					
						sprintf(szTmp,"both %s and %s were alive in city %d",
							pAttacker->GetName().c_str(),p->GetName().c_str(),nCityNo);
					else
						sprintf(szTmp,"both %s and %s were alive in city %d",
							p->GetName().c_str(),pAttacker->GetName().c_str(),nCityNo);
							
				}
				AddEvent(EVENT_FIGHT_RESULT, nCityNo, GetColor(),szTmp);  
				string s = pAttacker->Yell();
				if( s != "")
					AddEvent( EVENT_YELL, nCityNo,pAttacker-> GetColor(), s);						
				s = p->Yell();
				if( s != "" )
					AddEvent( EVENT_YELL, nCityNo, p->GetColor(), s);						
			}
		}
	}
}
void CHeadquarter::WolfsRob()
	{
	list<CWarrior * >::iterator i = lstWarrior.begin();
	for( i; i != lstWarrior.end();i ++) { //循环执行过程中有可能导致 lstWarrior中的某些元素被删，那么 这可能就有问题了 下面
		if( (*i)->nStrength <= 0)
			continue;
		if( (*i)->GetName().find("wolf") == string::npos )
			continue;
		int nCityNo = ( * i )->GetPosition();
		CWarrior * p = pEnemyheadquarter->QueryCityWarrior(nCityNo);
		char szTmp[200];
		if( p ) {
			if( p->GetName().find("wolf") != string::npos )
				continue;
			string takenWeapons = (*i)->TakeEnemyWeapons(p,true);
			if ( takenWeapons != "") {
//blue wolf 2 took 3 bomb from red dragon 2 in city 4				
				sprintf(szTmp,"%s took %s from %s in city %d",
					(*i)->GetName().c_str(),takenWeapons.c_str(),p->GetName().c_str(),nCityNo);				
				AddEvent(EVENT_WOLFSROB, nCityNo, GetColor(),szTmp);  				
			}
		}
	}
}

void CHeadquarter::AddEvent( EEventType eType, int nCityNo, int nColor, const string & sEventString)
{
	pKingdom->AddEvent( eType,nCityNo,nColor,sEventString);	
}
void CHeadquarter::PrintMoney() //addfor 2010
{		
		char szTmp[100];
		
		sprintf(szTmp,"%d",nMoney);
		string sEventString = string(szTmp) + " elements in " + GetColorStr() + " headquarter";
		if( nColor == COLOR_RED)  
			pKingdom->AddEvent( EVENT_PRINTMONEY, 0, nColor,sEventString);
		else 
			pKingdom->AddEvent( EVENT_PRINTMONEY, pKingdom->nCityNum + 1, nColor,sEventString);
}
void CHeadquarter::WarriorBorn()
{
	CWarrior * p = NULL;
	int nSeqIdx = (nWarriorNo - 1) % 5;
	if( nMoney <  CWarrior::InitialLifeValue[MakingSeq[nColor][nSeqIdx]])
		return ;
	nMoney -= CWarrior::InitialLifeValue[MakingSeq[nColor][nSeqIdx]];
	int nKindNo = MakingSeq[nColor][nSeqIdx];
	
	switch( nKindNo ) {
		case DRAGON:
			p = new CDragon(nWarriorNo,CWarrior::InitialLifeValue[nKindNo],CWarrior::InitalForce[nKindNo],nCityNo, this);
			break;
		case NINJA:
			p = new CNinja(nWarriorNo,CWarrior::InitialLifeValue[nKindNo],CWarrior::InitalForce[nKindNo],nCityNo, this);
			break;
		case ICEMAN:
			p = new CIceman(nWarriorNo,CWarrior::InitialLifeValue[nKindNo],CWarrior::InitalForce[nKindNo],nCityNo, this);
			break;
		case LION:
			p = new CLion(nWarriorNo,CWarrior::InitialLifeValue[nKindNo],CWarrior::InitalForce[nKindNo],nCityNo, this);
			break;
		case WOLF:
			p = new CWolf(nWarriorNo,CWarrior::InitialLifeValue[nKindNo],CWarrior::InitalForce[nKindNo],nCityNo, this);
			break;
	}
	
	lstWarrior.push_back(p);
	string sEventString = p->GetName () + " born";
	if( nKindNo == LION )
		sEventString += "\nIts loyalty is " + MyIntToStr(((CLion*)p)->nLoyalty);
	pKingdom->AddEvent( EVENT_BORN, nCityNo, nColor,sEventString);
	nWarriorNo ++;
} 

void CKingdom::AddEvent( EEventType eType, int nCityNo,int nColor, const string & sEventString)
{
	CEvent tmp(eType, nTimeInMinutes, nCityNo,nColor,sEventString);
	vEvent.push_back(tmp);
	//addfor debug
//	tmp.Output();
	//gwend
}
int CWeapon::Attack(CWarrior * pEnemy) {	
	pEnemy->Hurted(GetForce());
	return 1;
}

const char * CWeapon::Names[WEAPON_NUM] = {"sword","bomb","arrow" };
const char * CWarrior::Names[WARRIOR_NUM] = { "dragon","ninja","iceman","lion","wolf" };
int CWarrior::InitialLifeValue [WARRIOR_NUM];	
int CWarrior::InitalForce [WARRIOR_NUM];
int CLion::nLoyaltyDec;
int CHeadquarter::MakingSeq[2][WARRIOR_NUM] = { { 2,3,4,1,0 },{3,0,1,2,4} };
int main()
{
	int nCases;
	int M,N,R,K,T;
//	freopen("C:\\diskd\\aMyClasses\\程序设计实习\\final_homework\\cplusplus\\warcraft\\war2.5\\data.in","r",stdin);

	//freopen("f:\\mydoc\\程序设计实习\\warcraft\\war3\\warcraft.in","r",stdin);
	//freopen("f:\\mydoc\\程序设计实习\\warcraft\\war3\\6.in","r",stdin);
	cin >> nCases;
	int nCaseNo = 1;
	while( nCases -- )  {
		cin >> M >> N >>  K >> T;
		CLion::nLoyaltyDec = K;
	//第二行：五个整数，依次是 dragon 、NINJA、iceman、lion、wolf 的初始生命值。它们都大于0小于等于100
		int i;
		for( i = 0;i < WARRIOR_NUM;i ++ )
			cin >> CWarrior::InitialLifeValue[i];
		for( i = 0;i < WARRIOR_NUM;i ++ )
			cin >> CWarrior::InitalForce[i];
		CKingdom MyKingdom(N,M);
		MyKingdom.Run(T);
		cout << "Case " << nCaseNo++ << ":" << endl;
		MyKingdom.OutputResult();
	}	
	return 0;
}
