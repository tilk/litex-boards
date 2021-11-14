#!/usr/bin/env python3

#
# This file is part of LiteX-Boards.
#
# Copyright (c) 2021 Florent Kermarrec <florent@enjoy-digital.fr>
# Copyright (c) 2021 Gwenhael Goavec-Merou <gwenhael.goavec-merou@trabucayre.com>
# SPDX-License-Identifier: BSD-2-Clause

import os
import argparse

from migen import *

from litex_boards.platforms import quicklogic_quickfeather

from litex.soc.cores.clock import *
from litex.soc.integration.soc_core import *
from litex.soc.integration.builder import *
from litex.soc.cores.led import LedChaser
from litex.soc.cores.gpio import *

# CRG ----------------------------------------------------------------------------------------------

class _CRG(Module):
    def __init__(self, platform, with_eos_s3=False):
        self.rst = Signal()
        self.clock_domains.cd_sys = ClockDomain()

        # # #

        if with_eos_s3:
            # Use clocks generated by the EOS-S3 CPU.
            self.comb += ClockSignal("sys").eq(ClockSignal("eos_s3_0"))
            self.comb += ResetSignal("sys").eq(ResetSignal("eos_s3_0") | self.rst)
        else:
            # Use clocks generated by the qlal4s3b_cell_macro.
            class Open(Signal): pass
            self.specials += Instance("qlal4s3b_cell_macro",
                o_Sys_Clk0     = self.cd_sys.clk,
                o_Sys_Clk0_Rst = self.cd_sys.rst,
                o_Sys_Clk1     = Open(),
                o_Sys_Clk1_Rst = Open(),
            )

# BaseSoC ------------------------------------------------------------------------------------------

class BaseSoC(SoCCore):
    def __init__(self, sys_clk_freq=int(10e6), with_led_chaser=True, with_gpio_in=True, **kwargs):
        platform = quicklogic_quickfeather.Platform()

        # SoCCore ----------------------------------------------------------------------------------
        kwargs["cpu_type"] = kwargs.get("cpu_type", None)
        kwargs["with_uart"] = False
        SoCCore.__init__(self, platform, sys_clk_freq,
            ident          = "LiteX SoC on QuickLogic QuickFeather",
            ident_version  = True,
            **kwargs)

        # CRG --------------------------------------------------------------------------------------
        self.submodules.crg = _CRG(platform, with_eos_s3=kwargs["cpu_type"] == "eos-s3")

        # Leds -------------------------------------------------------------------------------------
        if with_led_chaser:
            self.submodules.leds = LedChaser(
                pads         = platform.request_all("user_led"),
                sys_clk_freq = sys_clk_freq)

        # GPIOIn (Interrupt test) ------------------------------------------------------------------
        if with_gpio_in:
            self.submodules.gpio = GPIOIn(platform.request_all("user_btn_n"), with_irq=True)
            if kwargs["cpu_type"] == "eos-s3":
                self.irq.add("gpio", use_loc_if_exists=True)

# Build --------------------------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="LiteX SoC on Quicklogic QuickFeather")
    parser.add_argument("--build", action="store_true", help="Build bitstream")
    soc_core_args(parser)
    args = parser.parse_args()

    soc = BaseSoC(**soc_core_argdict(args))
    builder = Builder(soc, compile_software=False)
    builder.build(run=args.build)

if __name__ == "__main__":
    main()
