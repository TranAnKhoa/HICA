\ Test8 WDP
Minimize
 obj: 31.6258 x_gw0_r0 + 19.6052 x_gw0_r1 + 18.8461 x_gw0_r2 + 180.127 x_gw0_r3 + 15.4482 x_gw0_r4 + 42.7703 x_gw0_r5 + 41.8888 x_gw0_r6 + 39.8567 x_gw0_r7 + 193.852 x_gw0_r8 + 42.8708 x_gw0_r9 + 33.013 x_gw0_r10 + 184.81 x_gw0_r11 + 24.6205 x_gw0_r12 + 184.594 x_gw0_r13 + 30.8733 x_gw0_r14 + 184.308 x_gw0_r15 + 28.2219 x_gw1_r0 + 22.1677 x_gw1_r1 + 10.5429 x_gw1_r2 + 221.545 x_gw1_r3 + 21.4935 x_gw1_r4 + 41.2223 x_gw1_r5 + 38.1015 x_gw1_r6 + 34.6739 x_gw1_r7 + 233.202 x_gw1_r8 + 44.8791 x_gw1_r9 + 29.7361 x_gw1_r10 + 229.057 x_gw1_r11 + 32.2688 x_gw1_r12 + 31.6149 x_gw1_r13 + 224.294 x_gw1_r14 + 30.8217 x_gw1_r15 + 230.738 x_gw1_r16 + 6.1935 x_od0_r0 + 12.4491 z_o4 + 9.50088 z_o2 + 13.356 z_o1 + 17.2372 z_o3 + 23.9129 z_o0
Subject To
 cov_o0: x_gw0_r0 + x_gw0_r5 + x_gw0_r6 + x_gw0_r7 + x_gw0_r8 + x_gw0_r9 + x_gw1_r0 + x_gw1_r5 + x_gw1_r6 + x_gw1_r7 + x_gw1_r8 + x_gw1_r9 + z_o0 = 1
 cov_o1: x_gw0_r1 + x_gw0_r5 + x_gw0_r6 + x_gw0_r10 + x_gw0_r11 + x_gw0_r12 + x_gw1_r1 + x_gw1_r5 + x_gw1_r10 + x_gw1_r11 + x_gw1_r12 + x_gw1_r13 + z_o1 = 1
 cov_o2: x_gw0_r2 + x_gw0_r7 + x_gw0_r10 + x_gw0_r13 + x_gw0_r14 + x_gw1_r2 + x_gw1_r6 + x_gw1_r7 + x_gw1_r10 + x_gw1_r14 + x_gw1_r15 + x_od0_r0 + z_o2 = 1
 cov_o3: x_gw0_r3 + x_gw0_r8 + x_gw0_r11 + x_gw0_r13 + x_gw0_r15 + x_gw1_r3 + x_gw1_r8 + x_gw1_r11 + x_gw1_r14 + x_gw1_r16 + z_o3 = 1
 cov_o4: x_gw0_r4 + x_gw0_r9 + x_gw0_r12 + x_gw0_r14 + x_gw0_r15 + x_gw1_r4 + x_gw1_r9 + x_gw1_r12 + x_gw1_r13 + x_gw1_r15 + x_gw1_r16 + z_o4 = 1
 one_gw0: x_gw0_r0 + x_gw0_r1 + x_gw0_r2 + x_gw0_r3 + x_gw0_r4 + x_gw0_r5 + x_gw0_r6 + x_gw0_r7 + x_gw0_r8 + x_gw0_r9 + x_gw0_r10 + x_gw0_r11 + x_gw0_r12 + x_gw0_r13 + x_gw0_r14 + x_gw0_r15 <= 1
 one_gw1: x_gw1_r0 + x_gw1_r1 + x_gw1_r2 + x_gw1_r3 + x_gw1_r4 + x_gw1_r5 + x_gw1_r6 + x_gw1_r7 + x_gw1_r8 + x_gw1_r9 + x_gw1_r10 + x_gw1_r11 + x_gw1_r12 + x_gw1_r13 + x_gw1_r14 + x_gw1_r15 + x_gw1_r16 <= 1
 one_od0: x_od0_r0 <= 1
Binaries
 x_gw0_r0 x_gw0_r1 x_gw0_r2 x_gw0_r3 x_gw0_r4 x_gw0_r5 x_gw0_r6 x_gw0_r7 x_gw0_r8 x_gw0_r9 x_gw0_r10 x_gw0_r11 x_gw0_r12 x_gw0_r13 x_gw0_r14 x_gw0_r15 x_gw1_r0 x_gw1_r1 x_gw1_r2 x_gw1_r3 x_gw1_r4 x_gw1_r5 x_gw1_r6 x_gw1_r7 x_gw1_r8 x_gw1_r9 x_gw1_r10 x_gw1_r11 x_gw1_r12 x_gw1_r13 x_gw1_r14 x_gw1_r15 x_gw1_r16 x_od0_r0 z_o4 z_o2 z_o1 z_o3 z_o0
End