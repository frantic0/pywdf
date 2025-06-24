import sys
import os

sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from core.wdf import *
from core.circuit import Circuit

import matplotlib.pyplot as plt


class _Capacitor(Circuit):

    def __init__(
            self, 
            sample_rate: int, 
            cutoff: float
        ) -> None:

        self.fs = sample_rate
        self.cutoff = cutoff
        
        self.C = 47e-9                          # capacitance in Farads
        self.R = 1.0 / (2 * np.pi * self.C * self.cutoff)
        self.Vs = ResistiveVoltageSource(self.R)

        self.C1 = Capacitor(self.C, self.fs)
        self.S1 = SeriesAdaptor(self.Vs, self.C1)

        super().__init__(self.Vs, self.S1, self.C1)
        # super().__init__(self.Vs, self.Vs, self.C1)


    def process_sample_i_v(self, sample: float) -> float:
        """Process an individual sample with this circuit.

        Note: not every circuit will follow this general pattern, in such cases users may want to overwrite this function. See example circuits

        Args:
            sample (float): incoming sample to process

        Returns:
            (i, v) I-V tupple: processed sample
        """
        self.Vs.set_voltage(sample)
        self.Vs.accept_incident_wave(self.S1.propagate_reflected_wave())
        self.S1.accept_incident_wave(self.Vs.propagate_reflected_wave())

        return ( self.source.wave_to_voltage(), self.source.wave_to_current(), self.output.wave_to_current() ) 




if __name__ == "__main__":
    
    fs = 44100
    f = 4
    # duration = .25
    duration = 1.0

    cap = _Capacitor(fs, 1000)
   
    # cap.plot_freqz()
    # cap.plot_freqz_list(range(1000, 10000, 1000), cap.set_cutoff, param_label="cutoff")
    # cap.AC_transient_analysis()

    t = np.linspace(0, duration, int(fs * duration), endpoint=False)

    sine = np.sin(2 * np.pi * f * t)  

    y = cap.process_i_v_signals(sine)

    v, _, i  = zip(*y)

    _, ax = plt.subplots(nrows=1, ncols=1, figsize=(10, 6.5))
    ax.plot(sine, color="r", label="voltage across", alpha=0.75)
    ax.set_xlabel("sample")
    ax.set_ylabel("v[n]")
    color = 'tab:blue'
    ax2 = ax.twinx() 
    ax2.set_ylabel('i[n]', color=color)
    ax2.tick_params(axis='y', labelcolor=color)
    ax2.plot(i, color=color, label="current through", alpha=0.75)

    ax.set_title(loc="left", label="v[n] voltage across and i[n] current through capacitor C1 ")
    ax.legend()  
    ax2.legend()  
    ax.grid(True)

    plt.savefig("./tests/capacitor.png")
    plt.show()