
import sys
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np

script_path = Path(__file__).resolve()
src_dir = script_path.parent.parent

sys.path.append(str(src_dir))

from core.wdf import *
from core.circuit import Circuit


class RCLowPass(Circuit):

    def __init__(
            self, 
            sample_rate: int, 
            cutoff: float
        ) -> None:

        self.fs = sample_rate
        self.cutoff = cutoff
        self.gain = 1

        self.previous_i = 0        

        self.C = 1e-6
        # self.R = 1.0 / (2 * np.pi * self.C * self.cutoff)
        self.R = 1.0

        # self.R1 = Resistor(self.R)

        self.R1 = ResistiveVoltageSource(None, Rval=self.R)
        # self.R1 = ResistiveVoltageSource(None, Rval=self.R*.5)
        
        self.C1 = Capacitor(self.C, self.fs, alpha=0.0)         # Alpha transform param (0.0 Backward Euler; 1.0 Bilinear Transform)

        self.S1 = SeriesAdaptor(self.R1, self.C1)
        self.I1 = PolarityInverter(self.S1)
        self.Vs = IdealVoltageSource(self.I1)

        super().__init__(self.Vs, self.Vs, self.C1)
        # super().__init__(self.Vs, self.Vs, self.R1)



    def set_cutoff(self, new_cutoff: float):
        if self.cutoff != new_cutoff:
            self.cutoff = new_cutoff
            self.R = 1.0 / (2 * np.pi * self.C * self.cutoff)
            self.R1.set_resistance(self.R)


    def process_sample(
        self, 
        sample: float
    ) -> float:

        print('i: ', self.previous_i)

        self.previous_i = self.R1.wave_to_current()

        # self.R1.set_voltage( self.previous_i * self.R*.5 )      # works well
        self.R1.set_voltage( self.previous_i * -10 )               # blows up 
        # self.R1.set_voltage( self.previous_i * 100 )            # blows up !!!
        # self.R1.set_voltage( sample + self.previous_i * self.R )  # returns 0.0s 

        self.previous_i = self.R1.wave_to_current()

        # self.R1.set_voltage(sample)
        # print('s: ', sample)
# 
        return super().process_sample(sample)

        # return ( 
        #     super().process_sample(sample),
        #     self.previous_i,
        #     self.R1.wave_to_current(),            
        #     )      



if __name__ == "__main__":
    
    # set params
    fs = 100e3
    frequency = 500
    decibels = 0
    switch_closed = True

    lpf = RCLowPass(fs, 1000)
    
    # plot transfer function
    plt_dir = src_dir.parent / "tests" / "plots"
    plt_dir.mkdir(exist_ok=True, parents=True)
    out_path = plt_dir / f"{script_path.stem}_{frequency}Hz.png"
    
    # lpf.plot_freqz( 
    #     outpath="tests/rc_lowpass_freqz.png" 
    #     )
    
    # lpf.plot_freqz_list(
    #     range(1000, 10000, 1000), 
    #     lpf.set_cutoff, 
    #     param_label="cutoff",
    #     outpath="tests/rc_lowpass_freqz_list.png"
    #     )
    
    # lpf.AC_transient_analysis(
    #     freq = 1000,
    #     amplitude = 1,
    #     t_ms = 5,
    #     outpath="tests/rc_lowpass_ac_analysis.png"
    #     )
    
    # lpf.plot_impulse_response( 
    #     outpath="tests/rc_lowpass_impulse_response.png" 
    #     )
    

    # a = np.ones(1)  # impulse signal
    # b = np.zeros(24000) 
    # samples = np.concatenate((a, b))

    duration = .005  # sec
    t = np.linspace(0, duration, int(fs * duration), endpoint=False)    # 1 period, 48000 points
    samples = np.sin(2 * np.pi * frequency * t)  # 1 period of samples of a f sign

    # lpf.set_cutoff(500)

    # generate sinusoid
    out = lpf.process_signal(samples)
    # out = out - 1  # remove DC offset [0, 2]

    # x, y, z = zip(*out) 

    plt.figure(figsize=(10, 4))
    # plt.plot(x, y, z)
    plt.plot(out )
    plt.xlim([0, 1000])
    plt.title(f"LPF {frequency}Hz sinewave")
    plt.tight_layout()
    out_path = plt_dir / f"{script_path.stem}_signal.png"
    plt.savefig(out_path.with_suffix('.png'))
    plt.show()

    print("done")