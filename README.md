# 性能测试 trace

**NOTE**: 这个不是官方的 `golden_trace`。

```shell
$ ls -1sh **/*.txt
2.1M bitcount/bitcount.txt
 11M bubble_sort/bubble_sort.txt
 24M coremark/coremark.txt
 14M crc32/crc32.txt
2.9M dhrystone/dhrystone.txt
9.8M quick_sort/quick_sort.txt
9.4M select_sort/select_sort.txt
 11M sha/sha.txt
940K stream_copy/stream_copy.txt
6.6M stringsearch/stringsearch.txt
```

包括完整的指令运行（来自 writeback 阶段的 debug 信号）、AXI 总线传输（来自 GS132 内部出来的 AXI 信号）。

目前发现抓取到的 AXI 传输次数比理论计算出的传输次数要多，原因不明。

## 仓库文件结构

* `README.md`：此文件。
* `.gitignore`
* `playground.ipynb`：一个简单分析抓取到的 trace 的 IPython Notebook（Jupyter）。
* `playground.py`：`playground.ipynb` 中的 Python 代码。
* `tracker.v`：trace 抓取的源码。
* `compiled/`：交叉编译后的二进制初始化文件，用于初始化仿真时的内存。
    * `*.mif`：Memory Initialization File。给 Vivado IP 用的。
* `stream_copy/`：测试点 `stream_copy`。
    * `stream_copy.s`：交叉编译后的反汇编文件。
    * `stream_copy.si`：`cat stream_copy.s | grep "9fc.....:" > stream_copy.si`。用于去除反汇编文件中的提示信息，只保留指令信息。
    * `stream_copy.lw`：`cat stream_copy.si | grep "lw" > stream_copy.lw`。所有 `lw*` 指令。
    * `stream_copy.sw`：`cat stream_copy.si | grep "sw" > stream_copy.sw`。所有 `sw*` 指令。
    * `stream_copy.txt`：抓取到的 trace。
* ...

## trace 内容说明
### AXI 记录

对于 AXI 的传输，tracker 只监听了 AW channel 和 AR channel。记录格式如下：

```
[物理地址],{aw/ar}
```

### CPU 记录

对于 GS132 CPU 的指令执行，用的是 `debug_wb_*` 信号。记录格式如下：

```
[debug_wb_pc],[debug_wb_rf_wen],[debug_wb_rf_wnum],[debug_wb_rf_wdata]
// PC 地址（虚拟地址），寄存器 write_enable，寄存器编号，写入数据
```

注意虚拟地址的映射规则（MIPS32 中 `kseg0` 和 `kseg1` 的映射规则）。

### 注意

由于 GS132 的一条指令貌似会执行多个 `cpu_clk` 的周期，导致 trace 内部很多指令的 `PC` 会被记录多次。例如：

```
...
1fc00d20,ar
9fc00d20,f,1d,9fc11204
9fc00d20,0,1d,9fc11204
1fc00b14,ar
9fc00b14,f,11,00000001
9fc00b14,0,11,00000001
1fc00b18,ar
9fc00b18,f,02,9fc010b1
9fc00b18,0,02,9fc010b1
...
```

`PC` 为 `0x9fc00b14` 的指令就被记录了 2 次。

## trace 抓取

将 `tracker.v` 的内容加入到 GS132 性能测试的 `mycpu_top.v` 的末尾，然后运行仿真。

注意修改 `tracker.v` 内的宏 `TRACE_SAVE_PATH`，这是抓取到的 trace 保存到的文件地址。

```verilog
`define TRACE_SAVE_PATH "/home/riteme/Code/nscscc/trace/perf_trace.txt"
```

如果发现 trace 文件末尾疑似不完整，请考虑在合适的位置加上 `$fclose(trace_file)`。例如：

```verilog
// mycpu_tb.v 的第 258 行
debug_end <= 1'b1;
$display("==============================================================");
$display("Test end!");
#40;
$fclose(trace_ref);
$fclose(trace_file);  // 加在这里，以确保文件全部写入到本地。
if (global_err)
begin
    $display("Fail!!!Total %d errors!",err_count);
end
```

## Playground

`stream_copy`：

```
x1faf_read_count: 7
x1faf_write_count: 155
x1fc_read_count: 18197
x1fc_write_count: 1202
instr_count: 14867
sw_count: 1199
lw_count: 3191
```

`x1faf_*` 和 `x1fc_*` 分别代表物理地址开头为 `0x1faf` 和 `0x1fc` 的读写。