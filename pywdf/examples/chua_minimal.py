import matplotlib.pyplot as plt
from pathlib import Path
import sys

script_path = Path(__file__).resolve()
src_dir = script_path.parent.parent

sys.path.append(str(src_dir))

from core.wdf import *
from core.circuit import Circuit



class ChuaMinimal(Circuit):
    def __init__(
        self, 
        sample_rate: int, 
        cutoff: float = 1000, 
        input_gain_db: float = 0,
        output_gain_db: float = 0
    ) -> None:

        self.fs = sample_rate
        self.cutoff = cutoff
        self.input_gain = 10 ** (input_gain_db / 20)
        self.input_gain_db = input_gain_db
        self.output_gain = 10 ** (output_gain_db / 20)
        self.output_gain_db = output_gain_db

        self.R = 2.5e3  # Ohms
        self.C = 1.0e-6
        self.L3_value = 7.07e-3     # L3 inductance

        self.L3 = Inductor(self.L3_value, self.fs)     
        self.R1 = Resistor(self.R)
        self.Vs = ResistiveVoltageSource()
        self.S1 = SeriesAdaptor(self.Vs, self.R1)
        self.C1 = Capacitor(self.C, self.fs)
        self.P1 = ParallelAdaptor(self.S1, self.C1)

        self.g1 = -500.0e-6 
        self.g2 = -800.0e-6
        self.v0 = 1.0
        self.R_NL = 569.2

        self.NL = ChuaDiode(
            self.S1, 
            g1=self.g1,         #  parameter 1
            g2=self.g2,         #  parameter 2
            v0=self.v0,         # Voltage parameter
            r1=self.R_NL,       # Resistance in Ohms
        )    
        
        # super().__init__(self.Vs, self.NL, self.C1)
        super().__init__(self.Vs, self.NL, self.NL)

    def process_sample(self, sample: float) -> float:
        sample *= self.input_gain
        return -( super().process_sample(sample) * self.output_gain) ### ¡! phase inverted !¡

if __name__ == "__main__":

    fs = 100e3
    frequency = 1000

    cm = ChuaMinimal(44100, cutoff=5000, input_gain_db=5)

    duration = 1.0
    t = np.linspace(0, duration, int(fs * duration), endpoint=False)
    sine = np.sin(2 * np.pi * frequency * t)  


    # out = cm.process_signal(np.ones((int(fs))))
    out = cm.process_signal(sine * 5.0)  # Use a sine wave as input signal

    # plot transfer function
    plt_dir = src_dir.parent / "tests" / "plots"
    plt_dir.mkdir(exist_ok=True, parents=True)
    out_path = plt_dir / f"{script_path.stem}.png"
 
    # _, ax = plt.subplots(nrows=1, ncols=1, figsize=(10, 6.5))
    

    plt.figure(figsize=(10, 4))
    plt.plot(out)
    plt.xlim([0, fs])
    plt.title(f"Chua diode output signal at {fs}Hz")
    plt.tight_layout()

    plt.savefig(out_path.with_suffix('.png'))
    plt.show()
