/**
 * tracker by riteme
 *
 * append this file to the end of module `mycpu_tb`
 * in the file `mycpu_tb.v` of performance test.
 */

`ifndef VERILATOR

`define TRACE_SAVE_PATH "/home/riteme/Code/nscscc/trace/perf_trace.txt"

integer trace_file;
initial begin
    trace_file = $fopen(`TRACE_SAVE_PATH, "w");
end

wire [31:0] last_wb_pc;
wire [3 :0] last_wb_rf_wen;
wire [4 :0] last_wb_rf_wnum;
wire [31:0] last_wb_rf_wdata;
reg [(32 + 4 + 5 + 32) - 1:0] last_vec;
wire [(32 + 4 + 5 + 32) - 1:0] debug_vec;
assign {last_wb_pc, last_wb_rf_wen, last_wb_rf_wnum, last_wb_rf_wdata} = last_vec;
assign debug_vec = {debug_wb_pc, debug_wb_rf_wen, debug_wb_rf_wnum, debug_wb_rf_wdata};

wire arvalid, arready, awvalid, awready;
wire [31:0] araddr, awaddr;
assign arvalid = soc_lite.cpu_arvalid;
assign arready = soc_lite.cpu_arready;
assign awvalid = soc_lite.cpu_awvalid;
assign awready = soc_lite.cpu_awready;
assign araddr = soc_lite.cpu_araddr;
assign awaddr = soc_lite.cpu_awaddr;

always @(posedge cpu_clk) begin
if (!resetn) begin
    last_vec <= 0;
end else if (!test_end && !debug_end) begin
    if (last_vec != debug_vec) begin
        $fdisplay(trace_file, "%h,%h,%h,%h",
            debug_wb_pc,
            debug_wb_rf_wen,
            debug_wb_rf_wnum,
            debug_wb_rf_wdata
        );
    end

    last_vec <= debug_vec;
end
end

always @(posedge cpu_clk) begin
    if (arready && arvalid) begin
        $fdisplay(trace_file, "%h,ar", araddr);
    end
    if (awready && awvalid) begin
        $fdisplay(trace_file, "%h,aw", awaddr);
    end
end

`endif