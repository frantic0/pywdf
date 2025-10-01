import matplotlib.pyplot as plt
from pathlib import Path
import sys

script_path = Path(__file__).resolve()
src_dir = script_path.parent.parent

sys.path.append(str(src_dir))

from core.wdf import *
from core.circuit import Circuit


class Chua(Circuit):

    def __init__(
        self,
        sample_rate: int,
        frequency: float = 442,
        decibels: float = -18,
        closed: bool = True,
    ) -> None:

        self.fs = sample_rate
        self.frequency = frequency
        self.decibels = decibels
        self.gain = self.decibels_to_gain()
        self.closed = closed

        # initialize wdf
        self.C1_value = 5.5e-9
        self.R2_value = 1.428e3
        self.L3_value = 7.07e-3
        self.C4_value = 49.5e-9

        self.C1 = Capacitor(self.C1_value, self.fs)    # fs, needs local discretization
        self.R2 = Resistor(self.R2_value)              # no need for discretization
        self.L3 = Inductor(self.L3_value, self.fs)     # fs, needs local discretization
        self.C4 = Capacitor(self.C4_value, self.fs)    # fs, needs local discretization

        # voltage injection with impulse for agitation ang getting oscillations started, given the system will always initialize with zeros, 
        # vInject(i) = wdf.series_voltage(i, button("impulse")*5 : ba.impulsify);
        self.Vs = ResistiveVoltageSource()
        # self.S2 = SeriesAdaptor(self.C4, self.Vs)
        # self.S2 = SeriesAdaptor(self.Vs, self.C4)
        # self.S2 = ParallelAdaptor(self.C4, self.Vs)
        self.P2 = ParallelAdaptor(self.L3, self.Vs)
        self.S1 = SeriesAdaptor(self.P2, self.R2)
        self.P1 = ParallelAdaptor(self.S1, self.C1 )

        self.g1 = -500.0e-6 
        self.g2 = -800.0e-6
        self.v0 = 1.0
        self.R_NL = 569.2

        self.NL = ChuaDiode(
            self.P1, 
            g1=self.g1,         #  parameter 1
            g2=self.g2,         #  parameter 2
            v0=self.v0,         # Voltage parameter
            r1=self.R_NL,       # Resistance in Ohms
        )     


        # self.S2 = SeriesAdaptor(self.C1, self.L1)
        # self.Vs = ResistiveVoltageSource()
        # self.S1 = SeriesAdaptor(self.Vs, self.S2)

        # self.SW1 = Switch(self.S1)

        # # init and set circuit
        # super().__init__(self.Vs, self.SW1, self.C1)
        # self.set_params(self.frequency, self.closed, self.decibels)

        # init and set circuit
        super().__init__(self.Vs, self.NL, self.C1)


    def process_sample(
        self, 
        sample: float
    ) -> float:
    
        self.Vs.set_voltage(sample)
        self.NL.accept_incident_wave(self.P1.propagate_reflected_wave())
        self.P1.accept_incident_wave(self.NL.propagate_reflected_wave())

        return self.output.wave_to_voltage()


    def process_sample_chua(self, sample: float) -> float:
        """Process an individual sample with this circuit.

        Note: not every circuit will follow this general pattern, in such cases users may want to overwrite this function. See example circuits

        Args:
            sample (float): incoming sample to process

        Returns:
            (i, v) I-V tupple: processed sample
        """
        self.Vs.set_voltage(sample)
        self.NL.accept_incident_wave(self.P1.propagate_reflected_wave())
        self.P1.accept_incident_wave(self.NL.propagate_reflected_wave())

        return self.output.wave_to_voltage(), self.C4.wave_to_voltage(), self.L3.wave_to_current() 




    def set_params(
        self, 
        frequency: float,
        decibels: float
    ) -> None:

        # update frequency
        if self.frequency != frequency:
            self.frequency = frequency

            # self.L = 1.0 / (np.square(self.twopi * frequency) * self.C)
            # self.L1.set_inductance(self.L)

        # update gain
        if self.decibels != decibels:
            self.decibels = decibels
            self.gain = self.decibels_to_gain()

    def decibels_to_gain(self):
        return 10 ** (self.decibels / 20.0)


if __name__ == "__main__":

    # set params
    fs = 48e3
    frequency = 440
    decibels = 0
   
    chua_circuit = Chua(fs)
    # chua_circuit.set_params(frequency, decibels)  # update params

    # plot transfer function
    plt_dir = src_dir.parent / "tests" / "plots"
    plt_dir.mkdir(exist_ok=True, parents=True)
    out_path = plt_dir / f"{script_path.stem}_{frequency}Hz.png"
    
    # chua_circuit.plot_freqz(
    #     out_path
    # )

    # chua_circuit.AC_transient_analysis(
    #     freq = 1000,
    #     amplitude = 1,
    #     t_ms = 5,
    #     outpath="tests/chua_ac_analysis.png"
    #     )

    # chua_circuit.plot_impulse_response(
    #     outpath="tests/chua_impulse_response.png"
    #     )
    # num_impulses = 4  # number of impulses to generate
    # impulse_frequency = 10  # duration of impulse signal in samples
    # # samples = np.zeros((int(impulse_frequency * fs / 1000)))  # 500 ms impulse signal
    # samples = np.zeros((int(impulse_frequency * num_impulses)))  # 500 ms impulse signal
    # samples[::impulse_frequency] = 1.0  # impulse signal

    a = np.ones(1)  # impulse signal
    b = np.zeros(500) 
    samples = np.concatenate((a, b))


    i_list, v1_list, v2_list = [], [], []

    for s in samples:
        v1, v2, i = chua_circuit.process_sample_chua(s)
        i_list.append(i)
        v1_list.append(v1)
        v2_list.append(v2)

    # Plotting
    fig, axes = plt.subplots(1, 3, figsize=(15, 4))
    axes[0].plot(v1_list, label='Amplitude C1 [V]', color='r')
    axes[1].plot(v2_list, label='Amplitude C4 [V]', color='g')
    axes[2].plot(i_list, label='Amplitude L3 [I]', color='b')

    for ax in axes:
        ax.legend()
        ax.grid(True)
        ax.set_xlabel("Sample [n]")

    axes[0].set_ylabel("Output")

    # Centered title
    fig.suptitle("Chua impulse response", fontsize=14)
    plt.tight_layout(rect=[0, 0, 1, 0.95])  # Leave space for suptitle

    # Save and show
    out_path = plt_dir / f"{script_path.stem}_signal.png"
    plt.savefig(out_path.with_suffix('.png'))
    plt.show()



