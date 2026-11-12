---
title: Linux 入门与基础命令
date: 2026-11-12
weight: 1
categories:
  - Linux
---

## 一、 Linux 历史与架构演进

### 1. 操作系统内核核心职责

内核（Kernel）主要负责管理：**进程调度、内存管理、文件系统、驱动、网络**。

### 2. 从 Unix 到 Linux

- **Unix 与 C 语言**：Unix 后来走向闭源商业化（如今 Unix 的正统继承者之一是 macOS），但它奠定了操作系统的三大底层理念：
  - **一切皆文件**（包括硬件设备、Socket、管道等）
  - **Pipe（管道）**（小型程序协同工作）
  - **多用户与隔离**
- **GNU 项目**：旨在打造一套自由的类 Unix 系统，提供了一系列关键组件与核心软件（如 `gcc` 编译器、`bash`、`gdb`、`glibc`），但官方内核（Hurd）迟迟未能广泛落地。
- **Linux 内核**：由 Linus Torvalds 按照 Unix 标准编写的开源操作系统内核，实现了内存管理、进程调度、文件系统、网络和设备驱动。
- **GNU/Linux 结合**：`GNU 套件 + Linux 内核` 共同构成了现代类 Unix 操作系统。

### 3. Linux 发行版生态

- **构成公式**：`Linux 发行版 = GNU 套件 + Linux 内核 + 包管理器 + （可选桌面环境和预装软件）`
- **主流派系**：
  - **Debian 系**：使用 `.deb` 包格式与 `apt` 包管理工具（代表：Ubuntu）。
  - **RedHat 系**：拥有强大的商业背书，使用 `.rpm` 包格式与 `dnf`/`yum` 包管理工具。

---

## 二、 常用基础命令速查

### 1. 目录与文件操作

- `cd -`：快速返回上一个工作目录。
- `touch`：更新文件时间戳。若对一个已存在的文件执行 `touch`，只会更新其时间戳（atime/mtime），**不会修改或清空文件内容**；若文件不存在则创建空文件。
- `file <filename>`：检查文件的真实类型（不依赖文件后缀名，通过魔数 Magic Number 识别）。

### 2. 文本查看与处理

- `less`：分页滚动查看大文件（按需加载，不一次性读入全部内存）。
- `head`：查看文件开头几行。
- `tail`：查看文件末尾几行（常配合 `-f` 实时追踪日志）。
- `join`：类似 SQL 的 `JOIN` 操作，基于共同字段合并两个已排序文件的行。

### 3. 历史命令与命令检索

- `history`：查看历史命令记录。
  - `!!`：直接执行上一条命令。
  - `!{index}`（如 `!103`）：直接执行历史记录中的第 103 条命令。
- `type`：查看命令的真实身份（区分是 Shell 内建命令还是外部二进制程序）。

  ```bash
  bakapiano@DESKTOP-NN9GVHM:/etc$ type cd
  cd is a shell builtin

  bakapiano@DESKTOP-NN9GVHM:/etc$ type docker
  docker is /usr/bin/docker
  ```

- `whatis`：查询命令的简短功能说明（基于简版手册页）。
- `whereis`：查找命令的二进制文件、源码和帮助手册页位置。

---

## 三、 Bash 管道、I/O 重定向与进程环境

### 1. 标准文件描述符（File Descriptors）

- `0`：`stdin`（标准输入）
- `1`：`stdout`（标准输出）
- `2`：`stderr`（标准错误输出）

### 2. 管道原则与三通管道

- **管道设计哲学**：Bash 使得每个程序只关注标准输入和标准输出，从而实现程序间的解耦。
- **`|`（匿名管道）**：将前一个命令的 `stdout` 直接连接到下一个命令的 `stdin`。
- **`tee`（三通管道）**：将 `stdin` 的数据同时分流输出到 `stdout` 和指定文件中，各保存/传递一份。
  ```bash
  xxx | tee temp.txt | xxx
  ```

### 3. 环境变量与子进程机制

- `env`：查看当前环境变量。环境变量跟随当前进程存在。
- **`fork` 与写时复制（COW, Copy-On-Write）**：当父进程 `fork` 创建子进程时，会复制父进程的环境变量与上下文信息，底层内存采用写时复制（COW）机制以优化性能。

---

## 四、 推荐学习资源

- [Linux Journey (EN)](http://linuxjourney.com/)

