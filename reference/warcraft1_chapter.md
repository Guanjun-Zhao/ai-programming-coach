# 第 1 章　用类建模：魔兽世界备战

在本章中，我们将解决一道经典的面向对象建模题——魔兽世界备战。题目要求模拟两个司令部按固定顺序循环生产武士，直到生命元耗尽为止，并按时间顺序打印每一个事件。

这道题本身并不复杂，但如果一开始就用全局变量各写一套，你会发现红方和蓝方的代码几乎是完全相同的复制——只有几个数字不同。用类封装之后，两个司令部只是同一套逻辑的两个实例，主函数会变得出奇地简洁。在本章中，你将学会定义 `Warrior` 和 `Headquarter` 两个相互关联的类，以及在 C++ 中处理类之间相互引用时用到的**前向声明**技术。

## 1.1　规划程序

在动手写代码之前，先来梳理程序要做的事：从第 0 小时开始，每小时让红方先、蓝方后各尝试生产一名武士；如果当前该造的武士造不起，就顺移到下一种；五种都造不起则宣告停产；双方都停产后本组数据结束。

据此可以确定核心分工：`Warrior` 负责记录自身属性并打印降生信息，`Headquarter` 负责管理生命元和生产顺序，主函数只需让两个司令部对象轮流调用 `Produce()` 就够了。

## 1.2　创建 Warrior 类

### 1.2.1　类的声明

下面来创建 `warcraft1.cpp`，先写好文件开头和 `Warrior` 类的声明。

文件开头引入 `iostream`、`cstdio`、`string` 三个头文件，定义常量 `WARRIOR_NUM = 5`。在 `Warrior` 类声明之前，单独写一行 `class Headquarter;`，这叫**前向声明**。`Warrior` 类内部需要保存一个指向 `Headquarter` 的指针，但 `Headquarter` 的完整定义还没出现。好在编译器只需知道"这是个类的名字"就能处理指针类型，不需要知道类里有什么，所以一行前向声明就够了。

`Warrior` 类的私有部分包含三个成员：指向所属司令部的指针 `pHeadquarter`、武士种类编号 `kindNo`，以及武士序号 `no`。武士打印降生消息时需要查询司令部的颜色和该类武士的现有数量，`pHeadquarter` 是唯一的通道。公开部分包含两个静态成员数组：字符串数组 `names` 存放五种武士的名称，整型数组 `initialLifeValue` 存放各种武士的初始生命值。这两个成员前面有 `static` 关键字，意味着它们属于整个类而不属于某一个武士对象——无论创建了多少名武士，这两张表在内存里只有一份，所有武士都从这里读取自己的属性。此外公开部分还有构造函数和 `PrintResult()` 方法的声明。

> **注意：** 静态成员变量必须在类外单独定义，否则编译能通过、链接会出错。你会在 1.5 节看到定义它们的三行代码。

### 1.2.2　构造函数

接下来实现 `Warrior` 的构造函数。构造函数接受三个参数：司令部指针 `p`、武士编号 `no_` 和种类编号 `kindNo_`。参数名比成员名多了一个下划线，这是 C++ 里常见的惯例——如果参数和成员同名，赋值语句 `no = no` 不会出错，但两边指的是同一个变量，什么也没赋到；多一个下划线就消除了这种歧义。函数体内将三个参数依次赋给 `no`、`kindNo` 和 `pHeadquarter`，武士从此刻起就"认识"自己的主人了。

### 1.2.3　打印降生消息

每当一名武士诞生，就要立刻打印一条消息。`PrintResult()` 接受当前小时数 `nTime` 作为参数，先调用 `pHeadquarter->GetColor()` 把颜色整数翻译成 `"red"` 或 `"blue"` 字符串，然后用 `printf` 按题目规定的格式输出一行。

输出内容依次是：三位补零的时间、阵营颜色、武士类型名称、武士编号、武士初始生命值、该类型武士当前已降生的数量（从 `pHeadquarter->warriorNum[kindNo]` 读取），最后是类型名称和 `in X headquarter` 结尾。由于 `printf` 不直接认识 C++ 的 `string` 类型，颜色和名称字符串都需要调用 `.c_str()` 转成 C 风格字符指针再传入。之所以能直接读取 `pHeadquarter->warriorNum[kindNo]` 这个私有成员，是因为我们稍后会在 `Headquarter` 里声明 `friend class Warrior`，允许武士访问司令部的私有数据。

> **注意：** `%03d` 的含义：`%d` 输出整数，`3` 表示最少显示 3 位，`0` 表示不足的位数用 0 补齐。数字 7 会输出为 `007`，数字 42 会输出为 `042`。这正是题目要求的时间格式。

## 1.3　创建 Headquarter 类

### 1.3.1　类的声明

`Headquarter` 类的私有部分共有七个成员。`totalLifeValue` 是剩余生命元，每生产一名武士就扣减一次。`stopped` 是一个布尔开关，一旦置为 `true`，以后每次调用 `Produce()` 都立即返回，不再做任何计算。`totalWarriorNum` 记录累计生产的武士总数。`color` 用整数表示阵营，0 代表红方、1 代表蓝方，用整数而非字符串是为了方便在二维数组里当下标使用。`curMakingSeqIdx` 是一个在 0 到 4 之间循环的索引，记录"下一个该轮到哪种武士"。整型数组 `warriorNum` 有五个元素，分别记录各类武士已生产的数量，`PrintResult()` 打印时需要读这里。最后，`pWarriors` 是一个最多容纳 1000 名武士的指针数组，用于持有动态创建的武士对象。

公开部分首先声明 `friend class Warrior`，打开了一扇让武士访问司令部私有数据的小门。静态二维数组 `makingSeq` 是一张 2×5 的查找表，第一维是阵营编号，第二维是生产顺序位置，每个元素存储武士的种类编号——这把题目里的"生产顺序"硬编码成了一张随时可查的表。此外还有 `Init()`、析构函数、`Produce()` 和 `GetColor()` 四个方法的声明。

### 1.3.2　初始化方法

题目有多组测试数据，同一对司令部对象需要反复重置，因此专门写一个 `Init()` 方法来做这件事，而不是依赖构造函数。`Init()` 接受颜色和初始生命元两个参数，将 `color`、`totalLifeValue`、`totalWarriorNum` 依次赋值，把 `stopped` 重置为 `false`（每组数据开始时司令部从"未停产"状态重新出发），把 `curMakingSeqIdx` 归零，并用循环把 `warriorNum` 的五个元素全部清零——否则上一组数据的计数会带到下一组里去，输出就全错了。

> **注意：** 这里用 `Init()` 而非构造函数，因为 C++ 的构造函数只在对象创建时调用一次，之后就不能再调了。`Init()` 是一个普通方法，可以在每组测试数据开始时反复调用，适合处理多组输入的题目。

### 1.3.3　析构函数

每名武士都是用 `new` 创建的，程序结束前需要逐一 `delete`。析构函数用一个循环遍历 `pWarriors` 指针数组，对 `totalWarriorNum` 范围内的每一个指针调用 `delete`，释放动态分配的内存。规则很简单：`new` 出来的东西，最终必须 `delete`，否则就是内存泄漏。析构函数会在对象生命期结束时（程序退出时）自动被调用。

## 1.4　让司令部生产武士

`Produce()` 是整个程序最关键的方法，我们分两步来看。

### 1.4.1　跳过造不起的武士

`Produce()` 一进入就先检查 `stopped` 标志，若已停产则立即返回 0，不做任何计算。

接下来是一个 `while` 循环，负责跳过当前造不起的武士。循环条件有两部分：其一，用 `makingSeq[color][curMakingSeqIdx]` 取出当前该轮到的武士种类编号，查 `initialLifeValue` 得到所需生命元，若大于剩余 `totalLifeValue` 则说明造不起；其二，`searchingTimes < WARRIOR_NUM` 保证最多转一整圈（5 次）就停下，不会无限循环。每次循环体内把 `curMakingSeqIdx` 加一并对 5 取模（让索引在 0 到 4 之间循环，如同钟表指针），同时把 `searchingTimes` 加一。

### 1.4.2　停产判断与正式生产

`while` 循环结束后，用 `makingSeq[color][curMakingSeqIdx]` 取出当前候选武士的种类编号存入 `kindNo`，然后再做一次判断：如果 `initialLifeValue[kindNo]` 仍然大于 `totalLifeValue`，说明转了整整一圈五种武士都造不起。此时把 `stopped` 置为 `true`，按颜色打印停产消息，返回 0。这次循环后的二次判断是必要的，因为循环本身无法区分"找到了造得起的武士"和"转完一圈都不够"这两种退出情况。

若通过了判断，则正式生产：先从 `totalLifeValue` 扣减该武士的生命值，把 `curMakingSeqIdx` 推进到下一位，用 `new` 创建武士对象并存入 `pWarriors` 数组（构造函数的第一个参数传 `this`，让武士认识自己的司令部；编号为 `totalWarriorNum + 1`，从 1 开始计数），递增 `warriorNum[kindNo]`，立即调用 `PrintResult()` 打印降生消息，最后递增 `totalWarriorNum` 并返回 1，告知主函数本轮成功生产了一名武士。

## 1.5　辅助函数与静态成员初始化

`GetColor()` 只有两行，根据 `color` 是 0 还是 1 返回 `"red"` 或 `"blue"` 字符串。它被好几处代码调用，专门写成方法可以避免到处重复写 `if (color == 0)`。

紧随其后是三行静态成员的类外定义。`Warrior::names` 用初始化列表直接赋值五种武士的名称，顺序与 `kindNo` 对应：0=dragon，1=ninja，2=iceman，3=lion，4=wolf。`Warrior::initialLifeValue` 只申请内存，真正的值会在主函数里通过 `scanf` 逐个填入。最值得停下来看一眼的是 `Headquarter::makingSeq` 的初始化：第一行 `{2,3,4,1,0}` 是红方的生产顺序（kindNo 2→3→4→1→0，即 iceman→lion→wolf→ninja→dragon），第二行 `{3,0,1,2,4}` 是蓝方的顺序。把题目里的文字描述翻译成编号序列，之后用 `makingSeq[color][curMakingSeqIdx]` 就能一步取到当前该生产哪种武士。

## 1.6　主函数

主函数把所有部件组装起来。`RedHead` 和 `BlueHead` 两个司令部对象在程序启动时各创建一次，贯穿整个运行过程，每组数据用 `Init()` 重置。

读入总组数 `t` 后，对每组数据：先打印 `Case:n`，读入生命元数量 `m` 和五种武士的初始生命值（直接写入静态成员 `Warrior::initialLifeValue`，之后所有武士对象都能读到），然后用 `Init(0, m)` 和 `Init(1, m)` 分别重置红蓝司令部。

内层循环每次先让红方调用 `Produce(nTime)`、再让蓝方调用，顺序与题目的输出要求完全一致。返回值分别用 `tmp1` 和 `tmp2` 接收，而不是直接写进 `&&` 条件里——这非常关键：如果把两次调用合并到一个 `if` 条件中，C++ 的短路求值规则会导致当红方返回 0 时蓝方根本不被调用，蓝方就漏掉了当轮的生产机会，输出将完全出错。只有当同一轮内 `tmp1` 和 `tmp2` 都是 0，即双方均已停产，循环才退出。

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
