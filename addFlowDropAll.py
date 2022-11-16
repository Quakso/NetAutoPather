import os
devices=['s1','s2','s3','s4','s5','s6','s7','s8','s9','s10','s11','s12','s13','s14','s15','s16','s17','s18']
for name in devices:
    os.system(f'sudo ovs-ofctl -O OpenFlow13 add-flow {name} "table=0,priority=6,dl_type=0x0800,actions=drop"')