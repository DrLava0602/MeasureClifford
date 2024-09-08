// Testbench for the D Flip-Flop
`define NUM_QUBITS 5
module tb_d_flip_flop;
    reg i_clk;
    reg i_rst_n;
    reg [1 : 0] i_basis_0;
    reg [1 : 0] i_basis_1;
    reg [1 : 0] i_basis_2;
    reg [1 : 0] i_basis_3;
    reg [1 : 0] i_basis_4;
    reg [1 : 0] i_result_0;
    reg [1 : 0] i_result_1;
    reg [1 : 0] i_result_2;
    reg [1 : 0] i_result_3;
    reg [1 : 0] i_result_4;
    wire [`NUM_QUBITS+1 : 0] o_value;
    wire o_ready;

    // Instantiate the D flip-flop module
    measureClifford mc(
        .i_clk(i_clk),
        .i_rst_n(i_rst_n),
        .i_basis_0(i_basis_0),
        .i_basis_1(i_basis_1),
        .i_basis_2(i_basis_2),
        .i_basis_3(i_basis_3),
        .i_basis_4(i_basis_4),
        .i_result_0(i_result_0),
        .i_result_1(i_result_1),
        .i_result_2(i_result_2),
        .i_result_3(i_result_3),
        .i_result_4(i_result_4),
        .o_value(o_value),
        .o_ready(o_ready)
    );

    // Clock generation: 50 MHz clock (20 ns period)
    initial begin
        i_clk = 0;          // Initialize clock to 0
        forever #10 i_clk = ~i_clk; // Toggle clock every 10 ns
    end
    // Stimulus block to apply test inputs
    initial begin
        // Initialize inputs
        i_rst_n = 0;
        i_basis_0 = 2'b01;
        i_basis_1 = 2'b10;
        i_basis_2 = 2'b01;
        i_basis_3 = 2'b01;
        i_basis_4 = 2'b10;
        i_result_0 = 2'b00;
        i_result_1 = 2'b00;
        i_result_2 = 2'b11;
        i_result_3 = 2'b11;
        i_result_4 = 2'b10;
        // Dump FSDB file
        $dumpfile("main.vcd"); // Specify the VCD file name
        $dumpvars(0, tb_d_flip_flop); // Dump all variables in the testbench
        // Apply reset for a few clock cycles
        #25 i_rst_n = 1;    // Release reset after 25 ns

        // Apply test inputs
        
        // End simulation after 200 ns
        #1000 $finish;
    end

    // Monitor signals
    // initial begin
    //     $monitor("Time: %0t | clk: %b | reset: %b | d: %b | q: %b", $time, clk, reset, d, q);
    // end

endmodule
