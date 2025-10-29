#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
如何使用?
1. 在BASE_STATS里找到对应角色, ***调整ATK里的608为你的武器白值***
2. ***修改main()里角色名***(角色全名(-xx), 不能是别名也不能有错别字), 初始词条, 当前词条
3. 修改精度delta, 可以计算提升多少词条的概率(一条6.6/3.3双爆是100*8.5,100是词条权重, 7/8/9/10对应四个档位)
4. 初始4 initial_substat_count=4, 初始3 initial_substat_count=3
5  填写约束(初始词条内), 如果你选定命中暴击爆伤 就填("暴击","暴伤")
6. 填写约束命中数2/3/4, 如果你想要计算选中词条至少命中2次的提升概率, 就填2
7. 运行代码, 会在gui生成图表, 也可修改参数以文件形式输出到同一目录

如何更新?
在BASE_STATS和ROLE_WEIGHTS加入新角色数据即可

更新在哪?
呃呃呃, 只能说优化了底层逻辑, 反正很厉害, 现在跑的巨快, 而且是精确值无误差, 当然平均成长和标准差有大概10^-5级别的误差

数据在哪?

https://github.com/yoimiya-kokomi/miao-plugin/blob/c174945eeccba9ffa98ba9cf35e076d02c76e9bc/resources/meta-gs/character/
这是角色基础数据, 打开这个网页找到新角色的名字打开dase.json, 就能看到三维数据了, 如果这个文件夹中还有artis.json, 那么说明这个角色有多种权重

https://github.com/yoimiya-kokomi/miao-plugin/blob/c174945eeccba9ffa98ba9cf35e076d02c76e9bc/resources/meta-gs/artifact/artis-mark.js
这是miao-plugin的全角色圣遗物副词条权重, 拉到最下面找到新角色按照相同格式添加即可

我为什么要做这个?

包里一大堆圣遗物, 想知道哪些圣遗物重roll提升概率高,  所以就自己写了, 其实技术含量很低，但是也写了一个晚上吧

初始词条怎么看?

微信小程序提瓦特工具坊, 把你要看的圣遗物挂在展柜然后更新就行, 第一个数据就是初始值

'''
from collections import defaultdict, Counter
from fractions import Fraction
from functools import reduce
from math import gcd, isclose, sqrt, comb
from typing import Dict, List, Tuple, Any, Optional
import os

# ---------------------------
# 用户可配置数据（按需修改）
# ---------------------------
BASE_STATS_RAW = {
    "七七": {"HP": 13247, "ATK": 351.59 + 608, "DEF": 987.81},
    "丝柯克": {"HP": 13300, "ATK": 439.49 + 608, "DEF": 863.51},
    "丽莎": {"HP": 10232, "ATK": 290.58 + 608, "DEF": 612.98},
    "久岐忍": {"HP": 13139, "ATK": 266.59 + 608, "DEF": 802.71},
    "九条裟罗": {"HP": 10232, "ATK": 245.26 + 608, "DEF": 671.35},
    "云堇": {"HP": 11395, "ATK": 239.93 + 608, "DEF": 785.19},
    "五郎": {"HP": 10232, "ATK": 229.26 + 608, "DEF": 693.25},
    "伊安珊": {"HP": 11395, "ATK": 322.57 + 608, "DEF": 682.3},
    "伊法": {"HP": 10778, "ATK": 223.93 + 608, "DEF": 647.27},
    "伊涅芙": {"HP": 13510, "ATK": 404.33 + 608, "DEF": 886.56},
    "优菈": {"HP": 14166, "ATK": 418.98 + 608, "DEF": 804.25},
    "克洛琳德": {"HP": 13877, "ATK": 413.12 + 608, "DEF": 839.64},
    "八重神子": {"HP": 11109, "ATK": 416.05 + 608, "DEF": 609.15},
    "凝光": {"HP": 10464, "ATK": 266.59 + 608, "DEF": 612.98},
    "凯亚": {"HP": 12441, "ATK": 279.92 + 608, "DEF": 846.49},
    "刻晴": {"HP": 14034, "ATK": 395.54 + 608, "DEF": 856.11},
    "北斗": {"HP": 13953, "ATK": 282.58 + 608, "DEF": 693.25},
    "千织": {"HP": 12251, "ATK": 395.54 + 608, "DEF": 1020.74},
    "卡维": {"HP": 12790, "ATK": 293.25 + 608, "DEF": 802.71},
    "卡齐娜": {"HP": 12615, "ATK": 271.92 + 608, "DEF": 847.22},
    "可莉": {"HP": 11018, "ATK": 380.89 + 608, "DEF": 658.54},
    "嘉明": {"HP": 12208, "ATK": 378.55 + 608, "DEF": 751.62},
    "坎蒂丝": {"HP": 11627, "ATK": 266.59 + 608, "DEF": 729.73},
    "埃洛伊": {"HP": 11673, "ATK": 286.54 + 608, "DEF": 724.4},
    "基尼奇": {"HP": 13772, "ATK": 407.26 + 608, "DEF": 858.58},
    "塔利雅": {"HP": 13371, "ATK": 237.26 + 608, "DEF": 598.38},
    "夏沃蕾": {"HP": 12790, "ATK": 242.59 + 608, "DEF": 646.54},
    "夏洛蒂": {"HP": 11511, "ATK": 217.27 + 608, "DEF": 583.79},
    "多莉": {"HP": 13255, "ATK": 279.92 + 608, "DEF": 773.52},
    "夜兰": {"HP": 15477, "ATK": 298.85 + 542, "DEF": 586.93},
    "奇偶·女性": {"HP": 11627, "ATK": 266.59 + 608, "DEF": 729.73},
    "奇偶·男性": {"HP": 11627, "ATK": 266.59 + 608, "DEF": 729.73},
    "奈芙尔": {"HP": 13607, "ATK": 421.91 + 608, "DEF": 856.11},
    "妮露": {"HP": 16264, "ATK": 281.27 + 608, "DEF": 780.37},
    "娜维娅": {"HP": 13549, "ATK": 430.7 + 608, "DEF": 849.52},
    "安柏": {"HP": 10116, "ATK": 279.92 + 608, "DEF": 642.16},
    "宵宫": {"HP": 10887, "ATK": 395.54 + 608, "DEF": 658.54},
    "希格雯": {"HP": 14297, "ATK": 235.86 + 608, "DEF": 535.07},
    "希诺宁": {"HP": 13287, "ATK": 336.94 + 608, "DEF": 996.05},
    "恰斯卡": {"HP": 10493, "ATK": 424.84 + 608, "DEF": 658.54},
    "托马": {"HP": 11046, "ATK": 253.26 + 608, "DEF": 802.71},
    "提纳里": {"HP": 11621, "ATK": 328.15 + 608, "DEF": 675.01},
    "早柚": {"HP": 12674, "ATK": 306.57 + 608, "DEF": 796.14},
    "旅行者": {"HP": 11627, "ATK": 227.09 + 608, "DEF": 729.73},
    "林尼": {"HP": 11805, "ATK": 389.68 + 608, "DEF": 576.23},
    "枫原万叶": {"HP": 14297, "ATK": 363.31 + 608, "DEF": 864.34},
    "柯莱": {"HP": 10464, "ATK": 250.59 + 608, "DEF": 642.16},
    "梦见月瑞希": {"HP": 13641, "ATK": 263.69 + 608, "DEF": 810.83},
    "欧洛伦": {"HP": 9883, "ATK": 306.57 + 608, "DEF": 627.57},
    "流浪者": {"HP": 10887, "ATK": 401.4 + 608, "DEF": 650.31},
    "温迪": {"HP": 11280, "ATK": 322.29 + 608, "DEF": 716.17},
    "烟绯": {"HP": 9999, "ATK": 301.24 + 608, "DEF": 627.57},
    "爱可菲": {"HP": 14297, "ATK": 424.84 + 542, "DEF": 783.67},
    "爱诺": {"HP": 11976, "ATK": 303.91 + 608, "DEF": 649.46},
    "玛拉妮": {"HP": 16264, "ATK": 222.67 + 608, "DEF": 610.8},
    "玛薇卡": {"HP": 13444, "ATK": 439.49 + 741, "DEF": 847.87},
    "珊瑚宫心海": {"HP": 14428, "ATK": 287.13 + 608, "DEF": 703.82},
    "珐露珊": {"HP": 10232, "ATK": 246.59 + 608, "DEF": 671.35},
    "班尼特": {"HP": 13255, "ATK": 239.93 + 674, "DEF": 824.6},
    "琳妮特": {"HP": 13255, "ATK": 290.58 + 608, "DEF": 761.11},
    "琴": {"HP": 15740, "ATK": 292.99 + 608, "DEF": 823.18},
    "瑶瑶": {"HP": 13139, "ATK": 266.59 + 608, "DEF": 802.71},
    "瓦雷莎": {"HP": 13602, "ATK": 436.56 + 608, "DEF": 837.17},
    "甘雨": {"HP": 10493, "ATK": 410.19 + 608, "DEF": 675.01},
    "申鹤": {"HP": 13916, "ATK": 372.1 + 608, "DEF": 889.03},
    "白术": {"HP": 14297, "ATK": 235.86 + 608, "DEF": 535.07},
    "砂糖": {"HP": 9883, "ATK": 213.27 + 608, "DEF": 751.62},
    "神里绫人": {"HP": 14690, "ATK": 366.24 + 608, "DEF": 823.18},
    "神里绫华": {"HP": 13772, "ATK": 418.98 + 674, "DEF": 839.64},
    "米卡": {"HP": 13371, "ATK": 279.92 + 608, "DEF": 762.57},
    "纳西妲": {"HP": 11096, "ATK": 366.24 + 542, "DEF": 675.01},
    "绮良良": {"HP": 13022, "ATK": 279.92 + 608, "DEF": 583.79},
    "罗莎莉亚": {"HP": 13139, "ATK": 301.24 + 542, "DEF": 758.92},
    "胡桃": {"HP": 16658, "ATK": 130.38 + 608, "DEF": 938.42},
    "艾尔海森": {"HP": 14297, "ATK": 383.82 + 608, "DEF": 837.17},
    "艾梅莉埃": {"HP": 14533, "ATK": 410.19 + 608, "DEF": 782.02},
    "芙宁娜": {"HP": 16395, "ATK": 298.85 + 542, "DEF": 744.98},
    "芭芭拉": {"HP": 10464, "ATK": 199.94 + 608, "DEF": 715.14},
    "茜特菈莉": {"HP": 12460, "ATK": 155.28 + 608, "DEF": 817.42},
    "荒泷一斗": {"HP": 13772, "ATK": 278.34 + 608, "DEF": 1027.33},
    "莫娜": {"HP": 11149, "ATK": 351.59 + 608, "DEF": 699.7},
    "莱依拉": {"HP": 11860, "ATK": 271.92 + 608, "DEF": 700.54},
    "莱欧斯利": {"HP": 14559, "ATK": 380.89 + 608, "DEF": 817.42},
    "菈乌玛": {"HP": 11411, "ATK": 312.33 + 608, "DEF": 716.17},
    "菲林斯": {"HP": 13379, "ATK": 430.7 + 608, "DEF": 865.98},
    "菲米尼": {"HP": 12906, "ATK": 319.9 + 608, "DEF": 757.46},
    "菲谢尔": {"HP": 9825, "ATK": 306.57 + 608, "DEF": 634.87},
    "蓝砚": {"HP": 9883, "ATK": 314.57 + 608, "DEF": 620.27},
    "行秋": {"HP": 10930, "ATK": 253.26 + 454, "DEF": 810},
    "诺艾尔": {"HP": 12906, "ATK": 239.93 + 608, "DEF": 853.79},
    "赛索斯": {"HP": 10464, "ATK": 285.25 + 608, "DEF": 598.38},
    "赛诺": {"HP": 13379, "ATK": 389.68 + 608, "DEF": 920.31},
    "辛焱": {"HP": 11976, "ATK": 311.91 + 608, "DEF": 853.79},
    "达达利亚": {"HP": 14034, "ATK": 369.17 + 608, "DEF": 872.57},
    "迪卢克": {"HP": 13903, "ATK": 410.19 + 608, "DEF": 839.64},
    "迪奥娜": {"HP": 10232, "ATK": 266.59 + 608, "DEF": 642.16},
    "迪希雅": {"HP": 16789, "ATK": 325.22 + 608, "DEF": 672.54},
    "那维莱特": {"HP": 15740, "ATK": 255.19 + 608, "DEF": 617.38},
    "重云": {"HP": 11743, "ATK": 279.92 + 608, "DEF": 693.25},
    "钟离": {"HP": 15740, "ATK": 307.64 + 608, "DEF": 790.25},
    "闲云": {"HP": 11149, "ATK": 410.19 + 608, "DEF": 613.27},
    "阿蕾奇诺": {"HP": 14034, "ATK": 418.98 + 608, "DEF": 819.06},
    "阿贝多": {"HP": 14166, "ATK": 307.64 + 608, "DEF": 938.42},
    "雷泽": {"HP": 12790, "ATK": 293.25 + 608, "DEF": 802.71},
    "雷电将军": {"HP": 13825, "ATK": 413.12 + 608, "DEF": 845.4},
    "香菱": {"HP": 11627, "ATK": 282.58 + 608, "DEF": 715.14},
    "魈": {"HP": 13641, "ATK": 427.77 + 608, "DEF": 856.11},
    "鹿野院平藏": {"HP": 11395, "ATK": 282.58 + 608, "DEF": 731.19}
}

ROLE_WEIGHTS_RAW = {
    "芭芭拉": {"大生命": 100, "大攻击": 50, "大防御": 0, "暴击": 50, "暴伤": 50, "元素精通": 0, "伤害": 80, "物理": 0, "充能效率": 55, "治疗": 100},
    "芭芭拉-输出": {"大生命": 0, "大攻击": 75, "大防御": 0, "暴击": 100, "暴伤": 100, "元素精通": 75, "伤害": 100, "物理": 0, "充能效率": 30, "治疗": 0},
    "甘雨": {"大生命": 0, "大攻击": 75, "大防御": 0, "暴击": 100, "暴伤": 100, "元素精通": 75, "伤害": 100, "物理": 0, "充能效率": 30, "治疗": 0},
    "甘雨-永冻": {"大生命": 0, "大攻击": 75, "大防御": 0, "暴击": 100, "暴伤": 100, "元素精通": 0, "伤害": 100, "物理": 0, "充能效率": 55, "治疗": 0},
    "雷电将军": {"大生命": 0, "大攻击": 75, "大防御": 0, "暴击": 100, "暴伤": 100, "元素精通": 0, "伤害": 75, "物理": 0, "充能效率": 90, "治疗": 0},
    "雷电将军-精通": {"大生命": 0, "大攻击": 50, "大防御": 0, "暴击": 50, "暴伤": 50, "元素精通": 100, "伤害": 75, "物理": 0, "充能效率": 90, "治疗": 0},
    "神里绫人": {"大生命": 50, "大攻击": 75, "大防御": 0, "暴击": 100, "暴伤": 100, "元素精通": 0, "伤害": 100, "物理": 0, "充能效率": 30, "治疗": 0},
    "神里绫人-蒸发": {"大生命": 45, "大攻击": 60, "大防御": 0, "暴击": 100, "暴伤": 100, "元素精通": 60, "伤害": 100, "物理": 0, "充能效率": 30, "治疗": 0},
    "八重神子": {"大生命": 0, "大攻击": 75, "大防御": 0, "暴击": 100, "暴伤": 100, "元素精通": 75, "伤害": 75, "物理": 0, "充能效率": 55, "治疗": 0},
    "申鹤": {"大生命": 0, "大攻击": 100, "大防御": 0, "暴击": 50, "暴伤": 50, "元素精通": 0, "伤害": 80, "物理": 0, "充能效率": 100, "治疗": 0},
    "云堇": {"大生命": 0, "大攻击": 75, "大防御": 100, "暴击": 80, "暴伤": 80, "元素精通": 0, "伤害": 80, "物理": 0, "充能效率": 80, "治疗": 0},
    "云堇-输出": {"大生命": 0, "大攻击": 75, "大防御": 100, "暴击": 100, "暴伤": 100, "元素精通": 0, "伤害": 100, "物理": 0, "充能效率": 75, "治疗": 0},
    "荒泷一斗": {"大生命": 0, "大攻击": 50, "大防御": 100, "暴击": 100, "暴伤": 100, "元素精通": 0, "伤害": 100, "物理": 0, "充能效率": 30, "治疗": 0},
    "五郎": {"大生命": 0, "大攻击": 75, "大防御": 100, "暴击": 50, "暴伤": 50, "元素精通": 0, "伤害": 100, "物理": 0, "充能效率": 75, "治疗": 0},
    "班尼特": {"大生命": 100, "大攻击": 50, "大防御": 0, "暴击": 50, "暴伤": 50, "元素精通": 0, "伤害": 80, "物理": 0, "充能效率": 100, "治疗": 100},
    "枫原万叶": {"大生命": 0, "大攻击": 50, "大防御": 0, "暴击": 50, "暴伤": 50, "元素精通": 100, "伤害": 80, "物理": 0, "充能效率": 55, "治疗": 0},
    "枫原万叶-满命": {"大生命": 0, "大攻击": 75, "大防御": 0, "暴击": 100, "暴伤": 100, "元素精通": 100, "伤害": 100, "物理": 0, "充能效率": 55, "治疗": 0},
    "行秋": {"大生命": 0, "大攻击": 75, "大防御": 0, "暴击": 100, "暴伤": 100, "元素精通": 0, "伤害": 100, "物理": 0, "充能效率": 75, "治疗": 0},
    "行秋-蒸发": {"大生命": 0, "大攻击": 75, "大防御": 0, "暴击": 100, "暴伤": 100, "元素精通": 75, "伤害": 100, "物理": 0, "充能效率": 75, "治疗": 0},
    "钟离": {"大生命": 100, "大攻击": 30, "大防御": 0, "暴击": 40, "暴伤": 40, "元素精通": 0, "伤害": 80, "物理": 0, "充能效率": 55, "治疗": 0},
    "钟离-输出": {"大生命": 80, "大攻击": 75, "大防御": 0, "暴击": 100, "暴伤": 100, "元素精通": 0, "伤害": 100, "物理": 100, "充能效率": 30, "治疗": 0},
    "神里绫华": {"大生命": 0, "大攻击": 85, "大防御": 0, "暴击": 100, "暴伤": 100, "元素精通": 0, "伤害": 100, "物理": 0, "充能效率": 45, "治疗": 0},
    "香菱": {"大生命": 0, "大攻击": 75, "大防御": 0, "暴击": 100, "暴伤": 100, "元素精通": 75, "伤害": 100, "物理": 0, "充能效率": 75, "治疗": 0},
    "胡桃": {"大生命": 80, "大攻击": 50, "大防御": 0, "暴击": 100, "暴伤": 100, "元素精通": 75, "伤害": 100, "物理": 0, "充能效率": 0, "治疗": 0},
    "胡桃-核爆": {"大生命": 90, "大攻击": 50, "大防御": 0, "暴击": 0, "暴伤": 100, "元素精通": 90, "伤害": 100, "物理": 0, "充能效率": 0, "治疗": 0},
    "温迪": {"大生命": 0, "大攻击": 75, "大防御": 0, "暴击": 80, "暴伤": 80, "元素精通": 75, "伤害": 100, "物理": 0, "充能效率": 55, "治疗": 0},
    "珊瑚宫心海": {"大生命": 100, "大攻击": 50, "大防御": 0, "暴击": 0, "暴伤": 0, "元素精通": 75, "伤害": 100, "物理": 0, "充能效率": 55, "治疗": 100},
    "莫娜": {"大生命": 0, "大攻击": 75, "大防御": 0, "暴击": 100, "暴伤": 100, "元素精通": 75, "伤害": 100, "物理": 0, "充能效率": 75, "治疗": 0},
    "阿贝多": {"大生命": 0, "大攻击": 0, "大防御": 75, "暴击": 100, "暴伤": 100, "元素精通": 0, "伤害": 100, "物理": 0, "充能效率": 0, "治疗": 0},
    "迪奥娜": {"大生命": 100, "大攻击": 50, "大防御": 0, "暴击": 50, "暴伤": 50, "元素精通": 0, "伤害": 80, "物理": 0, "充能效率": 90, "治疗": 100},
    "优菈": {"大生命": 0, "大攻击": 100, "大防御": 0, "暴击": 0, "暴伤": 100, "元素精通": 0, "伤害": 40, "物理": 100, "充能效率": 55, "治疗": 0},
    "优菈-核爆": {"大生命": 0, "大攻击": 75, "大防御": 0, "暴击": 100, "暴伤": 100, "元素精通": 0, "伤害": 0, "物理": 100, "充能效率": 55, "治疗": 0},
    "达达利亚": {"大生命": 0, "大攻击": 75, "大防御": 0, "暴击": 100, "暴伤": 100, "元素精通": 75, "伤害": 100, "物理": 0, "充能效率": 30, "治疗": 0},
    "魈": {"大生命": 0, "大攻击": 75, "大防御": 0, "暴击": 100, "暴伤": 100, "元素精通": 0, "伤害": 100, "物理": 0, "充能效率": 55, "治疗": 0},
    "宵宫": {"大生命": 0, "大攻击": 75, "大防御": 0, "暴击": 100, "暴伤": 100, "元素精通": 75, "伤害": 100, "物理": 0, "充能效率": 0, "治疗": 0},
    "宵宫-纯火": {"大生命": 0, "大攻击": 85, "大防御": 0, "暴击": 100, "暴伤": 100, "元素精通": 0, "伤害": 100, "物理": 0, "充能效率": 0, "治疗": 0},
    "九条裟罗": {"大生命": 0, "大攻击": 75, "大防御": 0, "暴击": 100, "暴伤": 100, "元素精通": 0, "伤害": 100, "物理": 0, "充能效率": 100, "治疗": 0},
    "琴": {"大生命": 0, "大攻击": 85, "大防御": 0, "暴击": 50, "暴伤": 50, "元素精通": 0, "伤害": 80, "物理": 100, "充能效率": 75, "治疗": 100},
    "菲谢尔": {"大生命": 0, "大攻击": 75, "大防御": 0, "暴击": 100, "暴伤": 100, "元素精通": 75, "伤害": 100, "物理": 60, "充能效率": 0, "治疗": 0},
    "罗莎莉亚": {"大生命": 0, "大攻击": 75, "大防御": 0, "暴击": 100, "暴伤": 100, "元素精通": 0, "伤害": 70, "物理": 80, "充能效率": 30, "治疗": 0},
    "罗莎莉亚-融化": {"大生命": 0, "大攻击": 75, "大防御": 0, "暴击": 100, "暴伤": 100, "元素精通": 90, "伤害": 100, "物理": 80, "充能效率": 30, "治疗": 0},
    "可莉": {"大生命": 0, "大攻击": 75, "大防御": 0, "暴击": 100, "暴伤": 100, "元素精通": 75, "伤害": 100, "物理": 0, "充能效率": 30, "治疗": 0},
    "可莉-纯火": {"大生命": 0, "大攻击": 85, "大防御": 0, "暴击": 100, "暴伤": 100, "元素精通": 0, "伤害": 100, "物理": 0, "充能效率": 55, "治疗": 0},
    "凝光": {"大生命": 0, "大攻击": 75, "大防御": 0, "暴击": 100, "暴伤": 100, "元素精通": 0, "伤害": 100, "物理": 0, "充能效率": 30, "治疗": 0},
    "北斗": {"大生命": 0, "大攻击": 75, "大防御": 0, "暴击": 100, "暴伤": 100, "元素精通": 45, "伤害": 100, "物理": 0, "充能效率": 100, "治疗": 0},
    "刻晴": {"大生命": 0, "大攻击": 75, "大防御": 0, "暴击": 100, "暴伤": 100, "元素精通": 75, "伤害": 100, "物理": 100, "充能效率": 0, "治疗": 0},
    "托马": {"大生命": 100, "大攻击": 50, "大防御": 0, "暴击": 50, "暴伤": 50, "元素精通": 75, "伤害": 80, "物理": 0, "充能效率": 75, "治疗": 0},
    "迪卢克": {"大生命": 0, "大攻击": 75, "大防御": 0, "暴击": 100, "暴伤": 100, "元素精通": 75, "伤害": 100, "物理": 0, "充能效率": 0, "治疗": 0},
    "诺艾尔": {"大生命": 0, "大攻击": 50, "大防御": 90, "暴击": 100, "暴伤": 100, "元素精通": 0, "伤害": 100, "物理": 0, "充能效率": 70, "治疗": 0},
    "旅行者": {"大生命": 0, "大攻击": 75, "大防御": 0, "暴击": 100, "暴伤": 100, "元素精通": 0, "伤害": 100, "物理": 0, "充能效率": 55, "治疗": 0},
    "重云": {"大生命": 0, "大攻击": 75, "大防御": 0, "暴击": 100, "暴伤": 100, "元素精通": 75, "伤害": 100, "物理": 0, "充能效率": 55, "治疗": 0},
    "七七": {"大生命": 0, "大攻击": 75, "大防御": 0, "暴击": 30, "暴伤": 30, "元素精通": 0, "伤害": 100, "物理": 100, "充能效率": 55, "治疗": 100},
    "凯亚": {"大生命": 0, "大攻击": 75, "大防御": 0, "暴击": 100, "暴伤": 100, "元素精通": 0, "伤害": 100, "物理": 100, "充能效率": 30, "治疗": 0},
    "烟绯": {"大生命": 0, "大攻击": 75, "大防御": 0, "暴击": 100, "暴伤": 100, "元素精通": 75, "伤害": 100, "物理": 0, "充能效率": 30, "治疗": 0},
    "早柚": {"大生命": 0, "大攻击": 75, "大防御": 0, "暴击": 50, "暴伤": 50, "元素精通": 100, "伤害": 100, "物理": 0, "充能效率": 55, "治疗": 100},
    "安柏": {"大生命": 0, "大攻击": 75, "大防御": 0, "暴击": 100, "暴伤": 100, "元素精通": 75, "伤害": 100, "物理": 100, "充能效率": 0, "治疗": 0},
    "丽莎": {"大生命": 0, "大攻击": 75, "大防御": 0, "暴击": 100, "暴伤": 100, "元素精通": 30, "伤害": 100, "物理": 0, "充能效率": 75, "治疗": 0},
    "埃洛伊": {"大生命": 0, "大攻击": 75, "大防御": 0, "暴击": 100, "暴伤": 100, "元素精通": 0, "伤害": 100, "物理": 0, "充能效率": 0, "治疗": 0},
    "辛焱": {"大生命": 0, "大攻击": 75, "大防御": 75, "暴击": 100, "暴伤": 100, "元素精通": 0, "伤害": 100, "物理": 100, "充能效率": 0, "治疗": 0},
    "砂糖": {"大生命": 0, "大攻击": 50, "大防御": 0, "暴击": 50, "暴伤": 50, "元素精通": 100, "伤害": 80, "物理": 0, "充能效率": 75, "治疗": 0},
    "雷泽": {"大生命": 0, "大攻击": 75, "大防御": 0, "暴击": 100, "暴伤": 100, "元素精通": 0, "伤害": 100, "物理": 100, "充能效率": 0, "治疗": 0},
    "夜兰": {"大生命": 80, "大攻击": 0, "大防御": 0, "暴击": 100, "暴伤": 100, "元素精通": 0, "伤害": 100, "物理": 0, "充能效率": 55, "治疗": 0},
    "久岐忍": {"大生命": 100, "大攻击": 50, "大防御": 0, "暴击": 50, "暴伤": 50, "元素精通": 100, "伤害": 100, "物理": 0, "充能效率": 55, "治疗": 100},
    "鹿野院平藏": {"大生命": 0, "大攻击": 75, "大防御": 0, "暴击": 100, "暴伤": 100, "元素精通": 30, "伤害": 100, "物理": 0, "充能效率": 30, "治疗": 0},
    "提纳里": {"大生命": 0, "大攻击": 75, "大防御": 0, "暴击": 100, "暴伤": 100, "元素精通": 90, "伤害": 100, "物理": 0, "充能效率": 30, "治疗": 0},
    "柯莱": {"大生命": 0, "大攻击": 75, "大防御": 0, "暴击": 100, "暴伤": 100, "元素精通": 75, "伤害": 100, "物理": 0, "充能效率": 75, "治疗": 0},
    "赛诺": {"大生命": 0, "大攻击": 75, "大防御": 0, "暴击": 100, "暴伤": 100, "元素精通": 75, "伤害": 100, "物理": 0, "充能效率": 55, "治疗": 0},
    "坎蒂丝": {"大生命": 100, "大攻击": 50, "大防御": 0, "暴击": 100, "暴伤": 100, "元素精通": 0, "伤害": 95, "物理": 0, "充能效率": 75, "治疗": 0},
    "妮露": {"大生命": 100, "大攻击": 0, "大防御": 0, "暴击": 30, "暴伤": 30, "元素精通": 80, "伤害": 80, "物理": 0, "充能效率": 30, "治疗": 0},
    "妮露-蒸发": {"大生命": 100, "大攻击": 0, "大防御": 0, "暴击": 100, "暴伤": 100, "元素精通": 100, "伤害": 190, "物理": 0, "充能效率": 30, "治疗": 0},
    "纳西妲": {"大生命": 0, "大攻击": 55, "大防御": 0, "暴击": 100, "暴伤": 100, "元素精通": 100, "伤害": 100, "物理": 0, "充能效率": 55, "治疗": 0},
    "多莉": {"大生命": 100, "大攻击": 50, "大防御": 0, "暴击": 50, "暴伤": 50, "元素精通": 0, "伤害": 80, "物理": 0, "充能效率": 75, "治疗": 100},
    "莱依拉": {"大生命": 100, "大攻击": 0, "大防御": 0, "暴击": 50, "暴伤": 50, "元素精通": 0, "伤害": 80, "物理": 0, "充能效率": 35},
    "流浪者": {"大生命": 0, "大攻击": 80, "大防御": 0, "暴击": 100, "暴伤": 100, "元素精通": 0, "伤害": 100, "物理": 0, "充能效率": 35, "治疗": 0},
    "珐露珊": {"大生命": 0, "大攻击": 75, "大防御": 0, "暴击": 100, "暴伤": 100, "元素精通": 0, "伤害": 100, "物理": 0, "充能效率": 100, "治疗": 0},
    "瑶瑶": {"大生命": 100, "大攻击": 75, "大防御": 0, "暴击": 30, "暴伤": 30, "元素精通": 75, "伤害": 100, "物理": 0, "充能效率": 75, "治疗": 100},
    "艾尔海森": {"大生命": 0, "大攻击": 55, "大防御": 0, "暴击": 100, "暴伤": 100, "元素精通": 100, "伤害": 100, "物理": 0, "充能效率": 35, "治疗": 0},
    "迪希雅": {"大生命": 75, "大攻击": 75, "大防御": 0, "暴击": 100, "暴伤": 100, "元素精通": 100, "伤害": 100, "物理": 0, "充能效率": 55, "治疗": 0},
    "迪希雅-血牛": {"大生命": 100, "大攻击": 30, "大防御": 0, "暴击": 40, "暴伤": 40, "元素精通": 0, "伤害": 0, "物理": 0, "充能效率": 30, "治疗": 0},
    "米卡": {"大生命": 75, "大攻击": 55, "大防御": 0, "暴击": 50, "暴伤": 50, "元素精通": 0, "伤害": 75, "物理": 75, "充能效率": 55, "治疗": 100},
    "白术": {"大生命": 100, "大攻击": 0, "大防御": 0, "暴击": 30, "暴伤": 30, "元素精通": 50, "伤害": 80, "物理": 0, "充能效率": 100, "治疗": 100},
    "白术-满命": {"大生命": 100, "大攻击": 75, "大防御": 0, "暴击": 100, "暴伤": 100, "元素精通": 75, "伤害": 100, "物理": 0, "充能效率": 35, "治疗": 100},
    "卡维": {"大生命": 0, "大攻击": 75, "大防御": 0, "暴击": 100, "暴伤": 100, "元素精通": 75, "伤害": 100, "物理": 0, "充能效率": 75, "治疗": 0},
    "绮良良": {"大生命": 100, "大攻击": 50, "大防御": 0, "暴击": 50, "暴伤": 50, "元素精通": 0, "伤害": 80, "物理": 0, "充能效率": 30, "治疗": 0},
    "林尼": {"大生命": 0, "大攻击": 75, "大防御": 0, "暴击": 100, "暴伤": 100, "元素精通": 0, "伤害": 100, "物理": 0, "充能效率": 30, "治疗": 0},
    "琳妮特": {"大生命": 0, "大攻击": 75, "大防御": 0, "暴击": 100, "暴伤": 100, "元素精通": 0, "伤害": 100, "物理": 0, "充能效率": 75, "治疗": 0},
    "菲米尼": {"大生命": 0, "大攻击": 75, "大防御": 0, "暴击": 100, "暴伤": 100, "元素精通": 0, "伤害": 100, "物理": 100, "充能效率": 55, "治疗": 0},
    "那维莱特": {"大生命": 100, "大攻击": 0, "大防御": 0, "暴击": 100, "暴伤": 100, "元素精通": 0, "伤害": 100, "物理": 0, "充能效率": 55, "治疗": 0},
    "莱欧斯利": {"大生命": 0, "大攻击": 75, "大防御": 0, "暴击": 100, "暴伤": 100, "元素精通": 75, "伤害": 100, "物理": 0, "充能效率": 45, "治疗": 0},
    "芙宁娜": {"大生命": 100, "大攻击": 0, "大防御": 0, "暴击": 100, "暴伤": 100, "元素精通": 0, "伤害": 95, "物理": 0, "充能效率": 75, "治疗": 95},
    "芙宁娜-满命": {"大生命": 100, "大攻击": 30, "大防御": 0, "暴击": 100, "暴伤": 100, "元素精通": 75, "伤害": 95, "物理": 0, "充能效率": 75, "治疗": 95},
    "夏洛蒂": {"大生命": 0, "大攻击": 85, "大防御": 0, "暴击": 50, "暴伤": 50, "元素精通": 0, "伤害": 80, "物理": 0, "充能效率": 100, "治疗": 100},
    "娜维娅": {"大生命": 0, "大攻击": 75, "大防御": 0, "暴击": 100, "暴伤": 100, "元素精通": 0, "伤害": 100, "物理": 0, "充能效率": 55, "治疗": 0},
    "夏沃蕾": {"大生命": 100, "大攻击": 0, "大防御": 0, "暴击": 50, "暴伤": 50, "元素精通": 0, "伤害": 80, "物理": 0, "充能效率": 55, "治疗": 55},
    "闲云": {"大生命": 0, "大攻击": 100, "大防御": 0, "暴击": 50, "暴伤": 50, "元素精通": 0, "伤害": 80, "物理": 0, "充能效率": 100, "治疗": 75},
    "闲云-满命": {"大生命": 0, "大攻击": 100, "大防御": 0, "暴击": 100, "暴伤": 100, "元素精通": 0, "伤害": 100, "物理": 0, "充能效率": 30, "治疗": 0},
    "嘉明": {"大生命": 0, "大攻击": 75, "大防御": 0, "暴击": 100, "暴伤": 100, "元素精通": 75, "伤害": 100, "物理": 0, "充能效率": 55, "治疗": 0},
    "千织": {"大生命": 0, "大攻击": 50, "大防御": 75, "暴击": 100, "暴伤": 100, "元素精通": 0, "伤害": 100, "物理": 0, "充能效率": 55, "治疗": 0},
    "阿蕾奇诺": {"大生命": 0, "大攻击": 75, "大防御": 0, "暴击": 100, "暴伤": 100, "元素精通": 75, "伤害": 100, "物理": 0, "充能效率": 30, "治疗": 0},
    "赛索斯": {"大生命": 0, "大攻击": 30, "大防御": 0, "暴击": 100, "暴伤": 100, "元素精通": 100, "伤害": 100, "物理": 0, "充能效率": 55, "治疗": 0},
    "克洛琳德": {"大生命": 0, "大攻击": 100, "大防御": 0, "暴击": 100, "暴伤": 100, "元素精通": 30, "伤害": 100, "物理": 0, "充能效率": 35, "治疗": 0},
    "希格雯": {"大生命": 100, "大攻击": 0, "大防御": 0, "暴击": 100, "暴伤": 100, "元素精通": 0, "伤害": 95, "物理": 0, "充能效率": 30, "治疗": 100},
    "希格雯-输出": {"大生命": 100, "大攻击": 0, "大防御": 0, "暴击": 100, "暴伤": 100, "元素精通": 0, "伤害": 100, "物理": 0, "充能效率": 75, "治疗": 90},
    "艾梅莉埃": {"大生命": 0, "大攻击": 100, "大防御": 0, "暴击": 100, "暴伤": 100, "元素精通": 30, "伤害": 100, "物理": 0, "充能效率": 55, "治疗": 0},
    "卡齐娜": {"大生命": 0, "大攻击": 0, "大防御": 75, "暴击": 100, "暴伤": 100, "元素精通": 0, "伤害": 100, "物理": 0, "充能效率": 75, "治疗": 0},
    "玛拉妮": {"大生命": 100, "大攻击": 0, "大防御": 0, "暴击": 100, "暴伤": 100, "元素精通": 100, "伤害": 100, "物理": 0, "充能效率": 45, "治疗": 0},
    "基尼奇": {"大生命": 0, "大攻击": 85, "大防御": 0, "暴击": 100, "暴伤": 100, "元素精通": 0, "伤害": 100, "物理": 0, "充能效率": 50, "治疗": 0},
    "希诺宁": {"大生命": 0, "大攻击": 0, "大防御": 100, "暴击": 30, "暴伤": 30, "元素精通": 0, "伤害": 80, "物理": 0, "充能效率": 100, "治疗": 100},
    "希诺宁-输出": {"大生命": 0, "大攻击": 0, "大防御": 100, "暴击": 100, "暴伤": 100, "元素精通": 0, "伤害": 100, "物理": 0, "充能效率": 55, "治疗": 70},
    "恰斯卡": {"大生命": 0, "大攻击": 85, "大防御": 0, "暴击": 100, "暴伤": 100, "元素精通": 30, "伤害": 80, "物理": 0, "充能效率": 40, "治疗": 0},
    "欧洛伦": {"大生命": 0, "大攻击": 75, "大防御": 0, "暴击": 100, "暴伤": 100, "元素精通": 50, "伤害": 100, "物理": 0, "充能效率": 75, "治疗": 0},
    "玛薇卡": {"大生命": 0, "大攻击": 75, "大防御": 0, "暴击": 100, "暴伤": 100, "元素精通": 85, "伤害": 100, "物理": 0, "充能效率": 0, "治疗": 0},
    "茜特菈莉": {"大生命": 0, "大攻击": 50, "大防御": 0, "暴击": 50, "暴伤": 50, "元素精通": 100, "伤害": 80, "物理": 0, "充能效率": 100, "治疗": 0},
    "茜特菈莉-输出": {"大生命": 0, "大攻击": 50, "大防御": 0, "暴击": 100, "暴伤": 100, "元素精通": 100, "伤害": 80, "物理": 0, "充能效率": 100, "治疗": 0},
    "蓝砚": {"大生命": 0, "大攻击": 100, "大防御": 0, "暴击": 50, "暴伤": 50, "元素精通": 30, "伤害": 80, "物理": 0, "充能效率": 75, "治疗": 0},
    "梦见月瑞希": {"大生命": 0, "大攻击": 30, "大防御": 0, "暴击": 30, "暴伤": 30, "元素精通": 100, "伤害": 80, "物理": 0, "充能效率": 45, "治疗": 95},
    "伊安珊": {"大生命": 0, "大攻击": 100, "大防御": 0, "暴击": 50, "暴伤": 50, "元素精通": 0, "伤害": 80, "物理": 0, "充能效率": 100, "治疗": 0},
    "瓦雷莎": {"大生命": 0, "大攻击": 85, "大防御": 0, "暴击": 100, "暴伤": 100, "元素精通": 30, "伤害": 100, "物理": 0, "充能效率": 40, "治疗": 0},
    "爱可菲": {"大生命": 0, "大攻击": 100, "大防御": 0, "暴击": 100, "暴伤": 100, "元素精通": 0, "伤害": 95, "物理": 0, "充能效率": 75, "治疗": 95},
    "伊法": {"大生命": 0, "大攻击": 75, "大防御": 0, "暴击": 50, "暴伤": 50, "元素精通": 100, "伤害": 80, "物理": 0, "充能效率": 35, "治疗": 0},
    "丝柯克": {"大生命": 0, "大攻击": 100, "大防御": 0, "暴击": 100, "暴伤": 100, "元素精通": 0, "伤害": 100, "物理": 0, "充能效率": 0, "治疗": 0},
    "塔利雅": {"大生命": 100, "大攻击": 50, "大防御": 0, "暴击": 50, "暴伤": 50, "元素精通": 0, "伤害": 80, "物理": 0, "充能效率": 100, "治疗": 0},
    "伊涅芙": {"大生命": 0, "大攻击": 75, "大防御": 0, "暴击": 100, "暴伤": 100, "元素精通": 75, "伤害": 0, "物理": 0, "充能效率": 40, "治疗": 0},
    "菈乌玛": {"大生命": 0, "大攻击": 25, "大防御": 0, "暴击": 50, "暴伤": 50, "元素精通": 100, "伤害": 0, "物理": 0, "充能效率": 100, "治疗": 0},
    "菈乌玛-输出": {"大生命": 0, "大攻击": 50, "大防御": 0, "暴击": 100, "暴伤": 100, "元素精通": 100, "伤害": 0, "物理": 0, "充能效率": 100, "治疗": 0},
    "爱诺": {"大生命": 0, "大攻击": 75, "大防御": 0, "暴击": 100, "暴伤": 100, "元素精通": 75, "伤害": 100, "物理": 0, "充能效率": 40, "治疗": 0}
}

ALIASES = {
    "暴击率": "暴击", "暴击伤害": "暴伤", "攻击力%": "大攻击", "小攻": "小攻击", "小防": "小防御", "小生": "小生命",
    "生命值%": "大生命", "防御力%": "大防御", "元素充能效率": "充能效率", "精通": "元素精通",
    "暴": "暴击", "爆": "暴伤", "攻": "大攻击", "生": "大生命", "防": "大防御", "充": "充能效率", "精": "元素精通", "爆伤": "暴伤"
}

N_VALUES_RAW = {
    "暴击": 7.0/18.0,
    "暴伤": 7.0/9.0,
    "小攻击": 35.0/18.0,
    "大攻击": 7.0/12.0,
    "小生命": 239.0/8.0,
    "大生命": 7.0/12.0,
    "小防御": 2.3147,
    "大防御": 0.7288,
    "元素精通": 2.3312,
    "充能效率": 11.0/17.0
}

SMALL_TO_BIG = {"小攻击": "大攻击", "小生命": "大生命", "小防御": "大防御"}
SMALL_TO_BASEKEY = {"小攻击": "ATK", "小生命": "HP", "小防御": "DEF"}

TIERS = [7, 8, 9, 10]

TOL = 1e-12
SMALL_SET = set(SMALL_TO_BIG.keys())


# ---------------------------
# 规范化工具
# ---------------------------
def normalize_key(name: str) -> str:
    if not isinstance(name, str):
        return name
    s = name.strip()
    return ALIASES.get(s, s)


def normalize_role_weights(raw: Dict[str, Dict[str, float]]) -> Dict[str, Dict[str, float]]:
    out = {}
    for role, attrs in raw.items():
        norm = {}
        for k, v in attrs.items():
            nk = normalize_key(k)
            norm[nk] = float(v)
        out[role] = norm
    return out


def normalize_base_stats(raw: Dict[str, Dict[str, float]]) -> Dict[str, Dict[str, float]]:
    out = {}
    for role, attrs in raw.items():
        norm = {}
        for k, v in attrs.items():
            nk = normalize_key(k)
            norm[nk] = float(v)
            norm[k] = float(v)
        out[role] = norm
    return out


def normalize_n_values(raw: Dict[str, float]) -> Dict[str, float]:
    return {normalize_key(k): float(v) for k, v in raw.items()}

# ---------------------------
# 小词条等效权重
# ---------------------------


def compute_small_weight_equivalent(
    big_weight: float,
    n_small: float,
    big_base_value: float,
    n_big: float = 1.0,
    return_fraction: bool = False
) -> Any:
    if isclose(float(big_weight), 0.0):
        return Fraction(0, 1) if return_fraction else 0.0
    if big_base_value is None or isclose(float(big_base_value), 0.0):
        return Fraction(0, 1) if return_fraction else 0.0
    if isclose(float(n_big), 0.0) or isclose(float(n_small), 0.0):
        return Fraction(0, 1) if return_fraction else 0.0
    if return_fraction:
        bw = Fraction(str(float(big_weight))).limit_denominator()
        ns = Fraction(str(float(n_small))).limit_denominator()
        nb = Fraction(str(float(n_big))).limit_denominator()
        base_val = Fraction(str(float(big_base_value))).limit_denominator()
        base_factor = (ns * 100) / (base_val * nb)
        return bw * base_factor
    else:
        base_factor = (float(n_small) * 100.0) / \
            (float(big_base_value) * float(n_big))
        return float(big_weight) * base_factor

# ---------------------------
# preprocess 初始四条映射
# ---------------------------


def preprocess_initial_four(
    initial_keys: List[str],
    role_name: str,
    role_weights_norm: Dict[str, Dict[str, float]],
    base_stats_norm: Dict[str, Dict[str, float]],
    n_values_norm: Dict[str, float],
    *,
    verbose: bool = False,
    allow_prefix_fallback: bool = True
) -> Tuple[List[str], Dict[str, float]]:
    if len(initial_keys) != 4:
        raise KeyError("initial_keys must contain exactly four items")
    shorthand = {"攻": "大攻击", "小攻": "小攻击", "生": "大生命", "小生": "小生命",
                 "防": "大防御", "小防": "小防御", "暴": "暴击", "爆": "暴伤", "精": "元素精通", "充": "充能效率"}

    if role_name in role_weights_norm:
        role_use = role_name
    elif allow_prefix_fallback:
        head = role_name.split("-", 1)[0]
        role_use = head if head in role_weights_norm else None
    else:
        role_use = None

    if role_use is None:
        raise KeyError(
            f"Role weights for '{role_name}' not found. Available roles: {list(role_weights_norm.keys())}")
    role_attrs = role_weights_norm[role_use]

    if role_use not in base_stats_norm:
        if verbose:
            print(
                f"Warning: base stats for '{role_use}' not found; small substat conversions will fallback to 0")
        role_base = {}
    else:
        role_base = base_stats_norm[role_use]

    resolved: Dict[str, float] = {}
    for p in initial_keys:
        mapped = shorthand.get(p, p)
        mapped = normalize_key(mapped)
        if mapped in SMALL_TO_BIG:
            small = mapped
            big = SMALL_TO_BIG[small]
            big_norm = normalize_key(big)
            big_weight = float(role_attrs.get(big_norm, 0.0))
            n_small = float(n_values_norm.get(small, 0.0))
            n_big = float(n_values_norm.get(big_norm, 1.0)
                          ) if big_norm in n_values_norm else 1.0
            basekey = SMALL_TO_BASEKEY.get(small)
            base_val = None
            if basekey:
                base_val = role_base.get(basekey)
            small_w = compute_small_weight_equivalent(
                big_weight, n_small, base_val, n_big=n_big, return_fraction=False)
            resolved[small] = small_w
            if verbose:
                print(
                    f"mapped '{p}' -> '{small}' (small). big='{big_norm}', big_weight={big_weight}, base={base_val}, n_small={n_small}, small_w={small_w}")
        else:
            nm = mapped
            w = float(role_attrs.get(nm, 0.0))
            resolved[nm] = w
            if verbose:
                print(f"mapped '{p}' -> '{nm}'. weight={w}")

    used_nonzero = sorted(
        [k for k, v in resolved.items() if not isclose(v, 0.0)])
    explicit_weights_sub = {k: resolved[k] for k in used_nonzero}
    if verbose:
        print("=> resolved_all:", resolved)
        print("=> used (nonzero):", used_nonzero)
        print("=> explicit_weights_sub:", explicit_weights_sub)
    return used_nonzero, explicit_weights_sub

# ---------------------------
# 单位化评分函数
# ---------------------------


def compute_score_units_based(
    stats_model: Dict[str, float],
    n_values_norm: Dict[str, float],
    weights: Dict[str, float],
    *,
    weights_are_int: bool = False,
    return_units_map: bool = False
) -> Any:
    total = 0.0
    units_map = {}
    for k, v in stats_model.items():
        if k not in n_values_norm:
            raise KeyError(f"n value for '{k}' not found.")
        n_k = float(n_values_norm[k])
        units = 0 if isclose(n_k, 0.0) else int(round(float(v) / n_k))
        w = weights.get(k, 0.0)
        if weights_are_int:
            w = int(w)
        else:
            w = float(w)
        total += units * w
        units_map[k] = units
    return (total, units_map) if return_units_map else float(total)

# ---------------------------
# 支持构造：自动选择整数/分数路径
# ---------------------------


def gcd_list(vals: List[int]) -> int:
    vals2 = [abs(v) for v in vals if v != 0]
    return reduce(gcd, vals2, 0) if vals2 else 1


def lcm(a: int, b: int) -> int:
    return a // gcd(a, b) * b


def lcm_list(vals: List[int]) -> int:
    return reduce(lambda x, y: lcm(x, y), vals, 1)


def build_support_auto(
    used: List[str],
    explicit_weights_sub: Dict[str, float],
    tiers: List[int] = TIERS,
    small_set: set = SMALL_SET,
    tol: float = TOL
) -> Tuple[List[int], int, int, bool]:
    contains_small = any(u in small_set for u in used)
    candidate_vals = []
    for name in used:
        w = float(explicit_weights_sub.get(name, 0.0))
        if abs(w) < tol:
            continue
        for t in tiers:
            candidate_vals.append(t * w)
    if not candidate_vals:
        raise ValueError("support empty: no nonzero weights")
    all_integer = not contains_small and all(
        abs(round(v) - v) <= tol for v in candidate_vals)
    if all_integer:
        support_int = [int(round(v)) for v in candidate_vals]
        g = gcd_list(support_int) or 1
        support_reduced = [
            v // g for v in support_int] if g > 1 else support_int
        return support_reduced, 1, g, False
    fracs: List[Fraction] = []
    for name in used:
        w = explicit_weights_sub.get(name, 0.0)
        if abs(float(w)) < tol:
            continue
        fw = Fraction(str(float(w))).limit_denominator()
        for t in tiers:
            fracs.append(Fraction(t) * fw)
    denoms = [f.denominator for f in fracs]
    scale = lcm_list(denoms) if denoms else 1
    support_int = [int(f * scale) for f in fracs]
    g2 = gcd_list([abs(x) for x in support_int if x != 0]) or 1
    support_reduced = [v // g2 for v in support_int] if g2 > 1 else support_int
    return support_reduced, scale, g2, True

# ---------------------------
# 基本卷积与 PMF 统计（通用）
# ---------------------------


def support_counts(support_int: List[int]) -> Dict[int, int]:
    return dict(Counter(support_int))


def convolve_counts_sparse(support_count: Dict[int, int], R: int) -> Dict[int, int]:
    counts = {0: 1}
    items = list(support_count.items())
    for _ in range(R):
        new = defaultdict(int)
        for s, c in counts.items():
            for v, m in items:
                new[s + v] += c * m
        counts = new
    return dict(counts)


def counts_to_pmf_stats(counts: Dict[int, int], scale: int, gcd_factor: int) -> Tuple[Dict[float, float], float, float, int]:
    denom = sum(counts.values())
    pmf = {(k * gcd_factor) / scale: v / denom for k, v in counts.items()}
    mean = sum(x * p for x, p in pmf.items())
    mean_sq = sum((x * x) * p for x, p in pmf.items())
    var = mean_sq - mean * mean
    std = sqrt(var) if var > 0 else 0.0
    return dict(sorted(pmf.items())), mean, std, denom

# ---------------------------
# 补丁 A：candidate_pool based 的精确条件性替换实现
# ---------------------------


def convolve_counts_with_hits(
    candidate_pool: List[str],
    explicit_weights_sub: Dict[str, float],
    tiers: List[int],
    forced_set: set,
    used_fractional_flag: bool,
    scale: int,
    gcd_factor: int,
    R: int
) -> Dict[Tuple[int, int], int]:
    """
    基于 candidate_pool 构造单次候选项（均等抽取 candidate），并做 R 次卷积，同时跟踪 hit_count。
    返回 (score_int_reduced_key, hit_count) -> multiplicity（原始样本空间计数）。
    """
    single_count = defaultdict(int)
    for name in candidate_pool:
        nm = normalize_key(name)
        w = float(explicit_weights_sub.get(nm, 0.0))
        for t in tiers:
            if used_fractional_flag:
                val_frac = Fraction(str(float(w))).limit_denominator(
                ) * Fraction(t) * Fraction(scale)
                val_int = int(round(val_frac / gcd_factor))
            else:
                raw = t * w
                val_int = int(round(raw / gcd_factor))
            hit = 1 if nm in forced_set else 0
            single_count[(val_int, hit)] += 1

    if not single_count:
        return {}

    # [ ((val,hit), multiplicity), ... ]
    single_items_unique = list(single_count.items())

    counts = {(0, 0): 1}
    for _ in range(R):
        new = defaultdict(int)
        for (s_old, h_old), c_old in counts.items():
            for (val_hit), mult in single_items_unique:
                v, hit = val_hit
                new[(s_old + v, h_old + hit)] += c_old * mult
        counts = new
    return dict(counts)


def _make_A_B_counts_from_group(
    candidate_pool: List[str],
    explicit_weights_sub: Dict[str, float],
    tiers: List[int],
    forced_set: set,
    used_fractional_flag: bool,
    scale: int,
    gcd_factor: int
) -> Tuple[Dict[int, int], Dict[int, int]]:
    A = defaultdict(int)
    B = defaultdict(int)
    for name in candidate_pool:
        nm = normalize_key(name)
        w = float(explicit_weights_sub.get(nm, 0.0))
        for t in tiers:
            if used_fractional_flag:
                val_frac = Fraction(str(float(w))).limit_denominator(
                ) * Fraction(t) * Fraction(scale)
                val_int = int(round(val_frac / gcd_factor))
            else:
                raw = t * w
                val_int = int(round(raw / gcd_factor))
            if nm in forced_set:
                A[val_int] += 1
            else:
                B[val_int] += 1
    return dict(A), dict(B)


def _poly_conv(c1: Dict[int, int], c2: Dict[int, int]) -> Dict[int, int]:
    out = defaultdict(int)
    for v1, m1 in c1.items():
        for v2, m2 in c2.items():
            out[v1 + v2] += m1 * m2
    return dict(out)


def _poly_pow_conv(base_counts: Dict[int, int], exponent: int) -> Dict[int, int]:
    if exponent <= 0:
        return {0: 1}
    result = {0: 1}
    base = dict(base_counts)
    e = exponent
    while e > 0:
        if e & 1:
            result = _poly_conv(result, base)
        e >>= 1
        if e:
            base = _poly_conv(base, base)
    return result


def conditional_replace_counts(
    counts_orig: Dict[Tuple[int, int], int],
    A_counts: Dict[int, int],
    B_counts: Dict[int, int],
    R: int,
    min_hits: int,
    verbose: bool = False
) -> Dict[int, int]:
    A_pows = [None] * (R + 1)
    B_pows = [None] * (R + 1)
    A_pows[0] = {0: 1}
    B_pows[0] = {0: 1}
    for e in range(1, R + 1):
        A_pows[e] = _poly_pow_conv(A_counts, e) if A_counts else {0: 0}
        B_pows[e] = _poly_pow_conv(B_counts, e) if B_counts else {0: 0}

    counts_final = defaultdict(int)
    sum_orig = 0
    for (score_int, h), mult_orig in counts_orig.items():
        sum_orig += mult_orig
        if h >= min_hits:
            counts_final[score_int] += mult_orig
            continue

        need = min_hits - h
        remaining_non_targets = R - h
        if need <= 0:
            counts_final[score_int] += mult_orig
            continue
        if remaining_non_targets < need:
            counts_final[score_int] += mult_orig
            continue

        a_exp = h + need
        b_exp = remaining_non_targets - need
        convA = A_pows[a_exp] if a_exp >= 0 else {0: 0}
        convB = B_pows[b_exp] if b_exp >= 0 else {0: 0}

        internal_counts = defaultdict(int)
        total_internal = 0
        for va, ma in convA.items():
            for vb, mb in convB.items():
                internal_counts[va + vb] += ma * mb
                total_internal += ma * mb

        if total_internal == 0:
            counts_final[score_int] += mult_orig
            continue

        allocations = {v_out: mult_orig * (cnt_internal / total_internal)
                       for v_out, cnt_internal in internal_counts.items()}

        floor_alloc = {}
        remainders = []
        assigned = 0
        for v_out, alloc in allocations.items():
            fa = int(alloc // 1)
            floor_alloc[v_out] = fa
            rem = alloc - fa
            remainders.append((rem, v_out))
            assigned += fa
        remaining_to_assign = int(mult_orig - assigned)
        remainders.sort(reverse=True)
        idx = 0
        while remaining_to_assign > 0 and idx < len(remainders):
            _, v_out = remainders[idx]
            floor_alloc[v_out] += 1
            remaining_to_assign -= 1
            idx += 1
        if remaining_to_assign > 0:
            any_key = next(iter(floor_alloc.keys()))
            floor_alloc[any_key] += remaining_to_assign

        for v_out, add_count in floor_alloc.items():
            counts_final[v_out] += add_count

    sum_final = sum(counts_final.values())
    if sum_final != sum_orig:
        diff = sum_orig - sum_final
        if verbose:
            print(
                f"conditional_replace_counts: sum mismatch sum_final={sum_final} sum_orig={sum_orig} diff={diff}; applying correction")
        if diff > 0:
            maxk = max(counts_final.keys())
            counts_final[maxk] += diff
        elif diff < 0:
            maxk = max(counts_final.keys())
            counts_final[maxk] += diff
    return dict(counts_final)

# ---------------------------
# 绘图、summary 与主分析入口
# ---------------------------


def plot_pmf(
    pmf_readable: Dict[float, float],
    threshold: float,
    R: int,
    *,
    mode: str = "auto",
    backend: Optional[str] = None,
    filename: str = "pmf.png",
    verbose: bool = False
) -> Optional[callable]:
    if mode == "none":
        if verbose:
            print("plot_pmf: mode='none' -> skip")
        return None

    try:
        import matplotlib
        if backend:
            try:
                matplotlib.use(backend)
                if verbose:
                    print(f"plot_pmf: backend set to {backend}")
            except Exception as e:
                if mode == "gui":
                    raise RuntimeError(
                        f"plot_pmf: failed to set backend {backend}: {e}")
                if verbose:
                    print(
                        f"plot_pmf: failed to set backend {backend}, fallback: {e}")
        import matplotlib.pyplot as plt
        import numpy as np
    except Exception as e:
        if mode == "gui":
            raise RuntimeError(
                f"plot_pmf: unable to init matplotlib for GUI: {e}")
        if verbose:
            print(
                f"plot_pmf: matplotlib init failed, switching to save mode: {e}")
        mode = "save"

    x = list(pmf_readable.keys())
    if not x:
        if verbose:
            print("plot_pmf: empty pmf_readable -> nothing to plot")
        return None
    y = [pmf_readable[k] for k in x]

    xs = np.array(x)
    ys = np.array(y)
    cumsum = np.cumsum(ys)

    try:
        fig, ax = plt.subplots(figsize=(10, 5))
        width = (max(x) - min(x)) / 300.0 if len(x) > 1 else 1.0
        width = max(0.5, width)
        bars = ax.bar(xs, ys, width=width, color="#4A90E2", edgecolor="black")
        ax.axvline(threshold, color="red", linestyle="--",
                   label=f"threshold={threshold:.2f}")
        ax.set_title(f"R={R} roll added-score PMF")
        ax.set_xlabel("added score")
        ax.set_ylabel("probability")
        ax.legend()
        ax.grid(alpha=0.25)
        plt.tight_layout()

        # Annotation for click
        annot = ax.annotate("", xy=(0, 0), xytext=(15, 15), textcoords="offset points",
                            bbox=dict(boxstyle="round", fc="w"),
                            arrowprops=dict(arrowstyle="->"))
        annot.set_visible(False)

        def nearest_index(x_query: float) -> int:
            idx = int(np.abs(xs - x_query).argmin())
            return idx

        def update_annot(idx: int):
            score = xs[idx]
            prob = ys[idx]
            cum = float(cumsum[idx])
            annot.xy = (score, prob)
            annot.set_text(
                f"score={score:.2f}\nprob={prob:.8f}\ncum={cum:.6f}")
            annot.get_bbox_patch().set_alpha(0.95)
            annot.set_visible(True)
            fig.canvas.draw_idle()

        def on_click(event):
            if event.inaxes != ax:
                return
            xq = event.xdata
            if xq is None:
                return
            idx = nearest_index(xq)
            update_annot(idx)

        fig.canvas.mpl_connect("button_press_event", on_click)

    except Exception as e:
        if mode == "gui":
            plt.close('all')
            raise
        if verbose:
            print(f"plot_pmf: plotting failed; will try save fallback: {e}")

    if mode in ("save", "auto"):
        try:
            abs_path = os.path.abspath(filename)
            plt.savefig(filename, bbox_inches="tight")
            if verbose:
                print(f"PMF plot saved to {abs_path}")
        except Exception as e_save:
            if mode == "save":
                print(f"plot_pmf: failed to save PMF plot: {e_save}")
                plt.close()
                return None
            if verbose:
                print(f"plot_pmf: save failed, attempt GUI: {e_save}")

    if mode in ("gui", "auto"):
        try:
            if verbose:
                print("plot_pmf: showing GUI (blocking)...")
            plt.show()
        finally:
            try:
                plt.close()
            except Exception:
                pass
    else:
        try:
            plt.close()
        except Exception:
            pass


def print_summary(res: Dict[str, Any]) -> None:
    prob_frac = f"{res['numerator']}/{res['denominator']}"
    prob_pct = f"{res['probability_float']:.6%}"
    mean = f"{res['mean_added_score']:.6f}"
    std = f"{res['std_added_score']:.6f}"
    init = f"{res['initial_score']:.2f}"
    cur = f"{res['current_score']:.2f}"
    thr = f"{res['threshold']:.2f}"
    rng = f"{res['min_real']:.2f}..{res['max_real']:.2f}"
    print("=== Analysis summary ===")
    print(f"Used stats: {res['used']}")
    print(f"Initial score: {init}    Current score: {cur}    Threshold: {thr}")
    print(f"Support range (min..max): {rng}    R: {res['R']}")
    print(f"Probability (exact): {prob_frac}  (≈ {prob_pct})")
    print(f"Mean added score: {mean}    Std: {std}")
    print("========================")


def analyze_roll(
    used: List[str],
    explicit_weights_sub: Dict[str, float],
    n_values_norm: Dict[str, float],
    initial_score: float,
    current_score: float,
    initial_substat_count: int,
    delta: float = 0.0,
    inclusive: bool = False,
    tiers: List[int] = TIERS,
    small_set: set = SMALL_SET,
    tol: float = TOL,
    forced_pair: Optional[Tuple[str, str]] = None,
    min_hits: int = 0,
    candidate_pool: Optional[List[str]] = None,
    verbose: bool = False
) -> Dict[str, Any]:

    threshold = current_score - initial_score + float(delta)
    R = 4 if initial_substat_count == 3 else 5

    support_reduced, scale, gcd_factor, used_fractional_flag = build_support_auto(
        used, explicit_weights_sub, tiers=tiers, small_set=small_set, tol=tol)

    # candidate_pool default to initial_stats_values keys if not provided
    if candidate_pool is None:
        print("analyze_roll: candidate_pool not provided; defaulting to initial_stats_values keys")

    do_replace = forced_pair is not None and min_hits and min_hits > 0

    if do_replace:
        fp0 = normalize_key(forced_pair[0])
        fp1 = normalize_key(forced_pair[1])
        forced_set = {fp0, fp1}
        if verbose:
            print("analyze_roll: forced_pair normalized to",
                  forced_set, "min_hits=", min_hits)
            print("analyze_roll: candidate_pool (normalized):",
                  [normalize_key(x) for x in candidate_pool])

        counts_orig = convolve_counts_with_hits(
            candidate_pool=candidate_pool,
            explicit_weights_sub=explicit_weights_sub,
            tiers=tiers,
            forced_set=forced_set,
            used_fractional_flag=used_fractional_flag,
            scale=scale,
            gcd_factor=gcd_factor,
            R=R
        )
        if verbose:
            sample_items = list(counts_orig.items())[:20]
            print("analyze_roll: sample counts_orig (score_int,hit)->mult:", sample_items)
            print("analyze_roll: total_orig_count:", sum(counts_orig.values()))

        A_counts, B_counts = _make_A_B_counts_from_group(
            candidate_pool=candidate_pool,
            explicit_weights_sub=explicit_weights_sub,
            tiers=tiers,
            forced_set=forced_set,
            used_fractional_flag=used_fractional_flag,
            scale=scale,
            gcd_factor=gcd_factor
        )
        if verbose:
            print("analyze_roll: A_counts (sample keys):",
                  sorted(A_counts.keys())[:10])
            print("analyze_roll: B_counts (sample keys):",
                  sorted(B_counts.keys())[:10])

        counts_reduced = conditional_replace_counts(
            counts_orig, A_counts, B_counts, R, min_hits, verbose=verbose)
    else:
        sup_count = support_counts(support_reduced)
        counts_reduced = convolve_counts_sparse(sup_count, R)

    pmf_readable, mean, std, denom = counts_to_pmf_stats(
        counts_reduced, scale, gcd_factor)

    if inclusive:
        numer = sum(cnt for k_red, cnt in counts_reduced.items()
                    if ((k_red * gcd_factor) / scale) >= threshold)
        prob = sum(p for x, p in pmf_readable.items() if x >= threshold)
    else:
        numer = sum(cnt for k_red, cnt in counts_reduced.items()
                    if ((k_red * gcd_factor) / scale) > threshold)
        prob = sum(p for x, p in pmf_readable.items() if x > threshold)

    min_real = min(counts_reduced.keys()) * gcd_factor / scale
    max_real = max(counts_reduced.keys()) * gcd_factor / scale

    return {
        "used": used,
        "scale": scale,
        "gcd_factor": gcd_factor,
        "used_fractional_path": used_fractional_flag,
        "initial_score": initial_score,
        "current_score": current_score,
        "threshold": threshold,
        "R": R,
        "denominator": denom,
        "numerator": numer,
        "probability_float": prob,
        "mean_added_score": mean,
        "std_added_score": std,
        "pmf_readable": pmf_readable,
        "support_reduced": sorted(set(counts_reduced.keys())),
        "counts_reduced": counts_reduced,
        "min_real": min_real,
        "max_real": max_real
    }


def run_analysis(
    role_name: str,
    initial_substats: Dict[str, float],
    current_stats_values: Dict[str, float],
    initial_substat_count: int,
    delta: float = 0.0,
    plot_mode: str = "auto",
    plot_backend: Optional[str] = None,
    plot_filename: str = "pmf.png",
    forced_pair: Optional[Tuple[str, str]] = None,
    min_hits: int = 0,
    candidate_pool: Optional[List[str]] = None,
    verbose: bool = False
) -> Dict[str, Any]:

    role_weights_norm = normalize_role_weights(ROLE_WEIGHTS_RAW)
    base_stats_norm = normalize_base_stats(BASE_STATS_RAW)
    n_values_norm = normalize_n_values(N_VALUES_RAW)

    norm_initial_input = {normalize_key(k): float(
        v) for k, v in initial_substats.items()}
    norm_current_input = {normalize_key(k): float(
        v) for k, v in current_stats_values.items()}
    if verbose:
        print("norm_initial_input:", norm_initial_input)
        print("norm_current_input:", norm_current_input)

    initial_keys = list(initial_substats.keys())
    if len(initial_keys) != 4:
        raise ValueError(
            "initial_substats must contain exactly four items (四个初始词条)")

    current_keys = list(current_stats_values.keys())

    if len(current_keys) != 4:
        raise ValueError(
            "current_stats_values must contain exactly four items (四个初始词条)")

    used, explicit_weights_sub = preprocess_initial_four(
        initial_keys,
        role_name,
        role_weights_norm,
        base_stats_norm,
        n_values_norm,
        verbose=verbose,
        allow_prefix_fallback=True
    )

    used2, explicit_weights_sub2 = preprocess_initial_four(
        current_keys,
        role_name,
        role_weights_norm,
        base_stats_norm,
        n_values_norm,
        verbose=verbose,
        allow_prefix_fallback=True
    )

    initial_stats_filtered = {k: norm_initial_input.get(k, 0.0) for k in used}
    current_stats_filtered = {k: norm_current_input.get(k, 0.0) for k in used2}

    # candidate_pool default: normalized initial keys (so zero-weight candidates must be included explicitly)
    if candidate_pool is None:
        candidate_pool = [normalize_key(k) for k in initial_keys]

    if verbose:
        print("Used:", used)
        print("explicit_weights_sub:", explicit_weights_sub)
        print("candidate_pool:", candidate_pool)

    initial_score, initial_units = compute_score_units_based(
        initial_stats_filtered, n_values_norm, explicit_weights_sub, return_units_map=True)
    current_score, current_units = compute_score_units_based(
        current_stats_filtered, n_values_norm, explicit_weights_sub2, return_units_map=True)

    if verbose:
        print("DEBUG initial_units:", initial_units)
        print("DEBUG current_units:", current_units)
        print(f"DEBUG initial_score (units-based): {initial_score}")
        print(f"DEBUG current_score (units-based): {current_score}")

    res = analyze_roll(
        used=used,
        explicit_weights_sub=explicit_weights_sub,
        n_values_norm=n_values_norm,
        initial_score=initial_score,
        current_score=current_score,
        initial_substat_count=initial_substat_count,
        delta=delta,
        inclusive=False,
        tiers=TIERS,
        small_set=SMALL_SET,
        tol=TOL,
        forced_pair=forced_pair,
        min_hits=min_hits,
        candidate_pool=candidate_pool,
        verbose=verbose
    )

    print("Used:", res["used"])
    print("scale:", res["scale"], "gcd_factor:", res["gcd_factor"],
          "fractional_path:", res["used_fractional_path"])
    print("Initial score:", res["initial_score"])
    print("Current score:", res["current_score"])
    print("Threshold:", res["threshold"])
    print("R:", res["R"])
    print("Probability (exact): {}/{} ≈ {:.6%}".format(
        res["numerator"], res["denominator"], res["probability_float"]))
    print("Mean added score ≈ {:.6f}, std ≈ {:.6f}".format(
        res["mean_added_score"], res["std_added_score"]))
    print("Mean added rate ≈ {:.6%}".format(
        (res["mean_added_score"] + res["initial_score"]) / res["current_score"]))
    print("min_real:", res["min_real"], "max_real:", res["max_real"])

    if plot_mode != "none":
        plot_pmf(res["pmf_readable"], res["threshold"], res["R"], mode=plot_mode,
                 backend=plot_backend, filename=plot_filename, verbose=verbose)

    return res


# ---------------------------
# 示例（直接运行脚本时执行）
# ---------------------------
if __name__ == "__main__":

    # 这里是输入数据, 填入评分规则和初始词条数值、当前词条数值
    role = "玛薇卡"
    init_four = {"精":16, "暴":2.7, "小攻":14,"爆":7}
    current = {"精":56, "暴":6.6, "小攻":14,"爆":20.2}


    # 默认 candidate_pool = init_four keys（可在这里扩展以包含零权重其他候选）

    # 注释掉的是普通强化，即无保底的强化
    '''
    out = run_analysis(role, init_four, current, initial_substat_count=4, delta=0.0, plot_mode="none", verbose=True)
    print_summary(out)
    '''

    candidate_pool = list(init_four.keys())

    # 暴击爆伤改成你选中的两个词条，min_hits为必中次数2、3、4, 不需要出图可改 plot_mode="none"
    # delta 可调节阈值，例如调整delta=100*8.5,即为当前圣遗物多一条6.6%爆伤, 7/8/9/10分别对应四个档位, 100是词条权重
    # initial_substat_count 4表示初始四词条，3表示初始三词条
    out = run_analysis(role, init_four, current, initial_substat_count=4, delta=0.0,
                       plot_mode="gui",
                       forced_pair=("暴击", "暴伤"), min_hits=4,
                       candidate_pool=candidate_pool,
                       verbose=False)
    print_summary(out)
