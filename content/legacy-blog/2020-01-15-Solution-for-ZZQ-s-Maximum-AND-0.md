---
title: Solution for ZZQ's Maximum AND
date: '2020-01-15T14:33:33.000Z'
lastmod: '2020-03-28T04:14:09.080Z'
weight: 17
categories:
- 旧博客（算法竞赛）
aliases:
- /2020/01/15/Solution-for-ZZQ-s-Maximum-AND-0/
original_url: https://bakapiano.github.io/2020/01/15/Solution-for-ZZQ-s-Maximum-AND-0/
original_generator: Hexo
migrated_from: rendered HTML
---

[ZZQ’s Maximum AND](https://www.luogu.com.cn/problem/T115848)

idea by bakapiano

prepared by bakapiano

## 题意 {#题意}

在 $n$ 个数中选恰好 $k$ 个使得这 $k$ 个数 $and$ 起来的和最大。

## 题解 {#题解}

题目难度 easy\+

注意到位运算时各位的运算是相互独立的，因此我们可以将这 $n$ 个数拆成二进制并从高位到低位依次考虑。假设当前处理的是第 $i$ 位，我们首先统计在二进制下这一位是 $1$ 的数的个数 $num$，然后我们分两种情况进行讨论：

若 $k \leq num$，说明存在一种选数的方案使得这一位是 $1$，此时我们可以抛弃这一位是 $0$ 的那些数而仅保留这一位是 $1$ 的数，可以这么做的依据是如果我们选择了某一个该位是 $0$ 的数作为 $k$ 个数中的一个，那么这一位 $and$ 起来的结果必然是 $0$，但是考虑到低位无论如何组合都不可能比这一位是 $1$ 的结果更优，因此我们不可能选择这一位是 $0$ 的那些数作为我们选择的结果之一。

若 $k > num$，说明无论怎么选这一位 $and$ 的结果都必为 $0$，因此保留所有数并继续处理下一位即可。

时间复杂度 $O(nlogn)$，可以在规定时限内通过本题。

此外可以考虑一下 $m$ 组询问，每次询问给出 $k$ 的加强版怎么做：）

tag: 贪心 位运算

## 标称 {#标称}
```cpp
#include <bits/stdc++.h> 

using namespace std;

const int MAXN = 1e5+5;

int n,k;
int val[MAXN];
int solve()
{
    int ans=0;
    vector<int> a,b;
    for(int i=1;i<=n;i++) a.push_back(val[i]);
    for(int i=20;i>=0;i--)
    {
        int cnt=0;
        for(auto x:a) if(x&(1<<i)) cnt++;
        if(cnt>=k)
        {
            ans+=(1<<i);
            b.clear();
            for(auto x:a) if(x&(1<<i)) b.push_back(x);
            swap(a,b);
        }
    }
    return ans;
}
 
int main()
{
    scanf("%d%d",&n,&k);
    for(int i=1;i<=n;i++)
        scanf("%d",&val[i]);
    printf("%d\n",solve());
    return 0;
}
```
