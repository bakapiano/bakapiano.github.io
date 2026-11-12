---
title: Solution for ZZQ's Catforces
date: '2020-01-16T00:39:28.000Z'
lastmod: '2020-03-28T04:13:57.726Z'
weight: 16
categories:
- 旧博客（算法竞赛）
aliases:
- /2020/01/16/Solution-for-ZZQ-s-Catforces/
original_url: https://bakapiano.github.io/2020/01/16/Solution-for-ZZQ-s-Catforces/
original_generator: Hexo
migrated_from: rendered HTML
---

[ZZQ’s Catforces](https://www.luogu.com.cn/problemnew/show/T116274)

idea by Nanako \& bakapiano

prepared by bakapiano \& zzq

## 题意 {#题意}

本题的背景为一个简化版的 CF 赛制，$n$ 道题有一个初始分数 $a[i]$，掉分速度为 $b[i]$/每分钟 与与解题所需时间 $t[i]$，请你安排一个解题顺序使得得分：

$$
score = \sum_{i=1}^{n} (a_{i} - b_{i}*\sum_{j=1}^{i}t_{j})
$$

最大。

## 题解 {#题解}

题目难度 medium-

注意到 $\sum_{i=1}^{n}a_{i}$ 项与解题顺序无关，我们只需要最小化总掉分数即可。

首先我们任意安排一个解题顺序 $p_{1},…,p_{n}$，并尝试对当前得到的答案进行改进。设 $p$ 数组中**相邻**的两项为 $x,y(1 \leq x < y \leq n)$，易知交换相邻两项对其他题目的得分没有影响(因为对于除 $x,y$ 的任意题目 $i$ 来说 $\sum_{j=1}^{i}t_{j}$ 不变)，下面我们来推导在什么情况下交换 $x,y$ 两项能使得答案变得更优。

首先设 $pre = \sum_{j=1}^{x-1}t_{j}$

设交换前 $x,y$ 两项对答案的贡献：

$$
ans_{1}=a_{x}-b_{x}*(pre+t_{x})+a_{y}-b_{y}*(pre+t_{x}+t_{y})
$$

交换后的贡献：

$$
ans_{2}=a_{y}-b_{y}*(pre+t_{y})+a_{x}-b_{x}*(pre+t_{y}+t_{x})
$$

使答案更优的条件：

$$
ans1 < ans2
$$

化简可得：

$$
b_{x}*t_{y}<b_{y}*t_{x}
$$

即:

$$
t_{x}/b_{x} > t_{y}/b_{y}
$$

设$k_{i}=t_{i}/b_{i}$，注意到当 $k_{y}<k_{x}$ 时交换相邻两项会使答案更优，因此我们可以选择序列中 $k_{i}$ 最小的一项并把它不断往前交换来使答案变的更优，然后选 $k_{i}$ 次小的一项 … 重复上述操作直至序列中的 $k_{i}$ 变得非递减，此使得到的排列便是最优解题顺序。

因此只需将所有题目按 $t_{i}/b_{i}$ 的顺序排序，$O(n)$ 计算答案即可，总复杂度 $O(nlogn+n)$ 可以在规定时限内通过本题。

tag: 贪心 sort

### 标称 {#标称}

注意使用 $double$ 计算斜率可能会造成精度误差，sort 时使用自定义比较函数即可避免这一问题。

```cpp
#include <bits/stdc++.h> 

using namespace std;

typedef long long LL;

const int MAXN = 1e5+5;

/*----------head----------*/

int n;
struct pro{LL a,b,t;}p[MAXN];
LL s[MAXN],ans;
int main()
{
    scanf("%d",&n);
    fp(i,1,n)
        scanf("%lld%lld%lld",&p[i].a,&p[i].b,&p[i].t),ans+=p[i].a;
    sort(p+1,p+1+n,[](pro a,pro b){return a.t*b.b<b.t*a.b;});
    fp(i,1,n)
    {
        s[i]=s[i-1]+p[i].t;
        ans-=s[i]*p[i].b;
    }
    printf("%lld\n",ans);
    return 0;
}
```
