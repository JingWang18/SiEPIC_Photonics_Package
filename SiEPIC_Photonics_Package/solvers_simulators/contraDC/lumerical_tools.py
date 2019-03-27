"""
    lumerical_tools.py
    Contra-directional coupler Lumerical simulation flow
    see [] for documentation

    Author: Mustafa Hammood   ; mustafa@siepic.com   ; mustafa@ece.ubc.ca
    SiEPIC Kits Ltd. 2019     ; University of British Columbia
            
"""
#%% find lumapi 
import sys, os

# Lumerical Python API path on system
lumapi_path = 'C:/Program Files/Lumerical/INTERCONNECT/api/python'
dir_path = os.path.dirname(os.path.realpath(__file__))
if os.path.exists(os.path.join(lumapi_path,'lumapi.py')):
    print('Found lumapi path at' + ': ' +lumapi_path)
    sys.path.append(lumapi_path)
else:
    print('lumapi path does not exist, edit lumapi_path variable')
    
#os.chdir(lumapi_path)
import lumapi

#%% run MODE for dispersion analysis
def run_mode(contraDC, simulation_setup):
    mode = lumapi.open('mode')
    
    # feed parameters into model
    lumapi.evalScript(mode,"gap = %s; width_1 = %s; width_2 = %s; thick_Si = %s; period = %s;" 
                      % (contraDC.gap, contraDC.w1, contraDC.w2, contraDC.thick_si, contraDC.period))
    
    lumapi.evalScript(mode,"wavelength = %s; wavelength_stop = %s;" 
                      % (simulation_setup.lambda_start, simulation_setup.lambda_end))
    
    if contraDC.pol == 'TE':
        lumapi.evalScript(mode,"pol = 1;")
    elif contraDC.pol == 'TM':
        lumapi.evalScript(mode,"pol = 2;")
 
    if contraDC.slab == True:
        lumapi.evalScript(mode,"slab = 1;")
        lumapi.evalScript(mode,"thick_Slab = %s;" % (contraDC.thick_slab))
    else:
        lumapi.evalScript(mode,"slab = 0;")
        lumapi.evalScript(mode,"thick_Slab = 0;")

    # run dispersion analysis script
    lumapi.evalScript(mode,"cd('%s');"%dir_path)
    lumapi.evalScript(mode,'dispersion_2WG;')
    
    # contra-directional coupling
    neff_data = lumapi.getVar(mode, 'n_eff_data')
    lambda_fit = lumapi.getVar(mode, 'lambda_fit')
    ng_contra = lumapi.getVar(mode, 'ng0')
    
    # self-coupling
    ng1 = lumapi.getVar(mode, 'ng0_self1')
    ng2 = lumapi.getVar(mode, 'ng0_self2')
    lambda_self1 = lumapi.getVar(mode, 'self1_lambda')
    lambda_self2 = lumapi.getVar(mode, 'self2_lambda')
    
    lumapi.close(mode)
    
    return [neff_data, lambda_fit, ng_contra, ng1, ng2, lambda_self1, lambda_self2]

#%% run MODE for EME simulation of device
def run_EME(contraDC, simulation_setup):
    return

#%% run FDTD for bandstructure simulation of device
def run_FDTD(contraDC, simulation_setup):
    c = 299792458           #[m/s]
    frequency_start = c/simulation_setup.lambda_end
    frequency_end = c/simulation_setup.lambda_start
    
    fdtd = lumapi.open('fdtd')#,hide=True)
    filename = 'contraDC_bandstructure'
        
    lumapi.evalScript(fdtd,"load('%s'); setnamed('::model','gap',%s); setnamed('::model','ax',%s); setnamed('::model','sinusoidal',%s)" 
                      % (filename, contraDC.gap,  contraDC.period, contraDC.sinusoidal))
    
    if contraDC.slab == True:
        lumapi.evalScript(fdtd,"setnamed('::model','slab',1); setnamed('::model','slab_thickness',%s);" % (contraDC.thick_slab))
    
    if contraDC.sinusoidal == True:
        lumapi.evalScript(fdtd,"setnamed('::mode','sinusoidal',1);")
        
    lumapi.evalScript(fdtd,"setnamed('::model','bus1_width',%s); setnamed('::model','bus1_delta',%s); setnamed('::model','bus2_width',%s); setnamed('::model','bus2_delta',%s);setnamed('::model','si_thickness',%s);"
                      % (contraDC.w1, contraDC.dW1, contraDC.w2, contraDC.dW2, contraDC.thick_si))
    
    lumapi.evalScript(fdtd,"setnamed('::model','f1',%s); setnamed('::model','f2',%s)"
                      % (frequency_start, frequency_end))
    lumapi.evalScript(fdtd,"cd('%s');"%dir_path)
    lumapi.evalScript(fdtd,'kappa_bandstructure;')

    delta_lambda_contra = lumapi.getVar(fdtd,"delta_lambda")
    lambda_contra = lumapi.getVar(fdtd,"lambda0")
    
    delta_lambda_self1 = lumapi.getVar(fdtd,"delta_lambda_self1")
    delta_lambda_self2 = lumapi.getVar(fdtd,"delta_lambda_self2")
    
    lumapi.close(fdtd)
    
    return [delta_lambda_contra, delta_lambda_self1, delta_lambda_self2, lambda_contra]

#%% run MODE to generate S-parameters .dat file
def generate_dat( contraDC, simulation_setup, S_Matrix ):
    mode = lumapi.open('mode')
    
    # feed polarization into model
    if contraDC.pol == 'TE':
        lumapi.evalScript(mode,"mode_label = 'TE'; mode_ID = '1';")
    elif contraDC.pol == 'TM':
        lumapi.evalScript(mode,"mode_label = 'TM'; mode_ID = '2';")
        
    # run write sparams script
    lumapi.evalScript(mode,"cd('%s');"%dir_path)
    lumapi.evalScript(mode,'write_sparams;')
    
    lumapi.close(mode)
    return