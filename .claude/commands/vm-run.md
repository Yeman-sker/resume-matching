---
description: 在 Parallels 虚拟机里运行命令(SSH parallels@10.211.55.4,共享目录 /media/psf/resume-matching)
argument-hint: <要在虚拟机里运行的命令,如 bash scripts/start_all.sh>
allowed-tools: Bash(ssh *)
---

本项目代码在本机编辑,但**必须在 Parallels 虚拟机里运行**。请用 SSH 在虚拟机上执行下面的命令,不要在本机执行。

要在虚拟机里运行的命令:`$ARGUMENTS`

## 执行规则

- **连接**:`ssh parallels@10.211.55.4`(已配置免密,主机名 ubuntu-linux-2404)。
- **工作目录**:`/media/psf/resume-matching` —— Parallels 共享挂载,等同本机项目目录,文件实时双向同步(改完代码直接在 VM 跑,无需 scp/上传)。
- **必须用 login shell**:远程命令包一层 `bash -lc`,否则 `hdfs`/`spark-submit` 不在 PATH(非交互 SSH 不加载 hadoop 环境)。login shell 会自动带上 `JAVA_HOME=/opt/jdk8`、`HADOOP_HOME=/usr/local/hadoop`、`SPARK_HOME=/usr/local/spark`。一次性命令(hdfs 查询、构建、跑批处理脚本、curl 等)这样执行:

  ```bash
  ssh parallels@10.211.55.4 "bash -lc 'cd /media/psf/resume-matching && $ARGUMENTS'"
  ```

- **常驻服务**(如 `scripts/start_all.sh` 末尾是 `wait`、`streaming/streaming_supervisor.sh` 会一直占用前台):**不要前台阻塞执行,否则会卡住**。改用后台启动:

  ```bash
  ssh parallels@10.211.55.4 "bash -lc 'cd /media/psf/resume-matching && nohup <命令> > logs/run.log 2>&1 &'"
  ```

  启动后用 `curl`/查端口/`hdfs dfs -ls` 确认服务确实起来了,再反馈给我。

- 执行完把关键输出反馈给我;若报错,帮我定位原因(常见:Streaming checkpoint 未清理、端口被占用、HDFS 未启动)。
