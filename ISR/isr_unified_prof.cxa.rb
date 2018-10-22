# -*- coding: utf-8 -*-
# ISR2D benchmark
# Setup by L.Veen
# Based on settings used in Nikishova et al. (2018) CVET
# Also corresponds to Tahir et al. (2013) PLOS ONE, Case 2
# Re = 120, flow velocity = 0.48m/s, 110ųm deployment depth
# Fast initial endothelium recovery, full recovery at 23 days.

###############
# Environment #
###############

# Configure directories for kernels
#isr2d_bindir = ENV["ISR2D_HOME"] + '/build'
#util_bindir = File.dirname(__FILE__) + '/../../../util/build'
#ic_cache_dir = File.dirname(__FILE__) + '/ic_cache'

util_bindir = ENV["UTIL_BINDIR"]
isr2d_bindir = ENV["MUSCLE_KERNELS_DIR"]
ic_cache_dir = ENV["IC_CACHE"]

Muscle.LAST.add_classpath isr2d_bindir
Muscle.LAST.add_libpath isr2d_bindir
Muscle.LAST.add_classpath util_bindir
Muscle.LAST.add_libpath util_bindir

PROFILE = true
DEBUG_ALLINEA = false

####################
# Model components #
####################

# Initial Conditions generator kernel

if PROFILE
  initialConditions = NativeInstance.new('ic', 'map_kernel', args: "--profile --no-mpi #{isr2d_bindir}/ICgenerator")
else
  initialConditions = NativeInstance.new('ic', "#{isr2d_bindir}/ICgenerator")
end
  
# SMC2D kernel

if PROFILE
  smc = NativeInstance.new('smc', 'map_kernel', args: "--profile --no-mpi #{isr2d_bindir}/SMCController")
else
  smc = NativeInstance.new('smc', "#{isr2d_bindir}/SMCController")
end
# SMC2D output mapper
smc_out = Instance.new('smcout', 'muscle.core.kernel.DuplicationMapper')

# SMC2BF mapper
smc2bf = Instance.new('smc2bf', 'cxa.cxa3d.smc2bf.ObsArray2DeltaObs3D')

# Bulk flow kernel
# Using all cores or whatever MPI gives us
bf = MPIInstance.new('bf', "#{isr2d_bindir}/FlowController")
# Using a single core, overrides environment
#bf = MPIInstance.new('bf', "#{isr2d_bindir}/FlowController", {
#     :mpiexec_args => '-np 1 --bind-to none'})

#bf = Instance.new('bf', 'muscle.core.standalone.MPIKernel')

if PROFILE
  bf['mpiexec_command']='map_kernel'
  bf['mpiexec_args']='--profile mpiexec -np '+ENV["QCG_KERNEL_bf"]
elsif DEBUG_ALLINEA
  bf['mpiexec_command']='ddt'
  bf['mpiexec_args']='--offline mpiexec -np '+ENV["QCG_KERNEL_bf"]
else
  bf['mpiexec_command']='mpiexec'
  bf['mpiexec_args']='-np '+ENV["QCG_KERNEL_bf"]
end

#bf['mpiexec_command']='mpiexec'
#bf['mpiexec_args']='-np '+ENV["QCG_KERNEL_BF"]

#smc['mpiexec_command']='mpiexec'
#smc['mpiexec_args']='-np '+ENV["QCG_KERNEL_SMC"]


# BF2SMC mapper
bf2smc = Instance.new('bf2smc', 'cxa.cxa3d.bf2smc.BFPulsBoundary2SMCStress')

# Drug Diffusion kernel
dd = Instance.new('dd', 'kernel.DrugDiffusion.DiffusionController')

# DD2SMC mapper
dd2smc = Instance.new('dd2smc', 'cxa.cxa3d.dd2smc.DrugDiffusion2SMCController')


# Connection scheme
initialConditions.couple(smc, {'InitialSMCListOut' => 'InitialSMCListIn'})
initialConditions.couple(smc, {'InitialECListOut' => 'InitialECListIn'})

smc.couple(smc_out, {'CellPositionsOut' => 'In'})

smc_out.couple(smc2bf, {'Out1' => 'ObstaclesIn'}, ['cxa.cxa3d.smc2bf.Cells2Obstacles'])
smc_out.couple(bf2smc, {'Out2' => 'CellPositionsIn'})
smc_out.couple(dd, {'Out3' => 'NodeTypesIn'}, ['cxa.cxa3d.smc2dd.Cells2NodeTypes'])
smc_out.couple(dd2smc, {'Out4' => 'CellPositionsIn'})

smc2bf.couple(bf, {'InitialSolidOut' => 'InitialSolidIn'})
smc2bf.couple(bf, {'NewSolidOut' => 'NewSolidIn'})
smc2bf.couple(bf, {'NewFluidOut' => 'NewFluidIn'})

bf.couple(bf2smc, {'CoordinatesOut' => 'CoordinatesIn'})
bf.couple(bf2smc, {'LBLinksOut' => 'LBLinksIn'})
bf.couple(bf2smc, {'PressureOut' => 'PressureIn'})
bf.couple(bf2smc, {'ShearStressOut' => 'ShearStressIn'})
bf.couple(bf2smc, {'MaxShearStressOut' => 'MaxShearStressIn'})
bf.couple(bf2smc, {'AbsShearStressOut' => 'AbsShearStressIn'})
bf.couple(bf2smc, {'OsiOut' => 'OsiIn'})

bf2smc.couple(smc, {'CellMaxStressOut' => 'CellMaxStressIn'})
bf2smc.couple(smc, {'CellOsiOut' => 'CellOsiIn'})

dd.couple(dd2smc, {'LatticeCoordinatesOut' => 'LatticeCoordinatesIn'})
dd.couple(dd2smc, {'DrugConcentrationOut' => 'DrugConcentrationIn'})

dd2smc.couple(smc, {'CellDrugConcentrationOut' => 'CellDrugConcentrationIn'})



#######################
# Simulation settings #
#######################

$env["verbose"] = 1

## IC file locations
$env["ic_stage3_path"] = "#{ic_cache_dir}"
$env["ic_smc_hex"] = 1

## Time scales
$env['default_dt'] = 3600
$env['max_timesteps'] = 5 * 24 * 3600

$env["ic:dt"] = 0
$env["ic:T"] = 0

$env["smc:dt"] = 3600
$env["smc:T"] = 5 * 24 * 3600

$env["dd:dt"] = 500
$env["dd:T"] = 500

$env["bf:T"] = 0.01
$env["bf:dt"] = 0.0001


## Blood flow parameters
$env["bf:convergence_limit"] = 1e-3
$env["bf:use_0d_model"] = 0
$env["bf:flow_velocity[m/s]"] = 0.48

# Domain
$env["length[mm]"] = 1.5
$env["lumen_width[mm]"] = 1.0
$env["tunica_width[mm]"] = 0.121547
$env["total_width[mm]"] = 1.24309

## Discretization
$env["flowdx[mm]"] = 0.01
$env["dd_dx[mm]"] = 0.01
$env["xmin[mm]"] = 0.0
$env["ymin[mm]"] = -0.621547
$env["zmin[mm]"] = 0.0

# Bounding box
$env["xmin_bb[mm]"] = 0.0
$env["ymin_bb[mm]"] = -0.75
$env["zmin_bb[mm]"] = 0.0
$env["width_bb[mm]"] = 1.5

## Cell properties
$env["smc_mean_rad[mm]"] = 0.0151934
$env["smc_sigm_rad[mm]"] = 0.000
$env["ec_mean_rad[mm]"] = 0.00426935
$env["ec_sigm_rad[mm]"] = 0.000

## Strut properties
$env["strut_firstX[mm]"] = 0.749
$env["strut_spacing[mm]"] = 0.0
$env["strut_number"] = 1
$env["strut_side[mm]"] = 0.12
$env["max_deploy[mm]"] = 0.11                     # deployment depth

## SMC model properties
$env["solver_max_run_time"] = 5000                # fixed run time of physical solver, internal units
$env["solver_convergence_limit"] = 1.0e-3         # convergence limit for force equilibration
$env["compressive_hoop_stiffness"] = 1.0          # relative hoop stiffness in compressive regime
$env["png_width[px]"] = 400                       # width of png image produced
$env["strut_rep"] = "obstacle"                    # strut representation: boundary_element or obstacle

# Biology
$env["smc_max_strain"] = 1.0                      # threshold (hoop) strain for smc apoptosis/necrosis
$env["smc_max_stress"] = 1.0                      # threshold stress for smc apoptosis/necrosis
$env["iel_max_l_strain"] = 0.05                   # threshold (longitudinal) strain for iel breaking
$env["iel_max_h_strain"] = 0.095                  # threshold (hoop) strain for iel breaking
$env["iel_max_stress"] = 1.0                      # threshold stress for iel breaking
$env["smc_drug_conc_thresholdL"] = 0.35           # drug concentration threshold for smc proliferation
$env["smc_drug_conc_thresholdH"] = 0.35
$env["smc_OSI_thresholdL"] = 0.45
$env["smc_OSI_thresholdH"] = 0.5
$env["smc_wss_thresholdL"] = 0.276                # wss_max threshold for smc proliferation [Pa]
$env["smc_wss_thresholdH"] = 0.3
$env["ci_threshold_count"] = 4.5
$env["ci_weight_smc"] = 1
$env["ci_weight_iel"] = 3
$env["ci_weight_obstacle"] = 1

$env["ci_range_factor"] = 1.1                     # 1.2?
                                                  # Reendothelialisation (Tahir et al. (2013) Case-1)
$env["re_day0_ec_coverage"] = 0.0                 # initial ec coverage
$env["re_point1_time"] = 3.0 * 24.0 * 3600.0      # time of first coverage value
$env["re_point1_coverage"] = 0.59                 # coverage fraction at first time point
$env["re_recovered_time"] = 23.0 * 24.0 * 3600.0  # time of full recovery
$env["re_growth_correction"] = 1                  # disabled later by P. Zun
$env["re_reenable_cells"] = 1                     # backported later from ISR3D by P. Zun

# Parameters used by equilibration code
$env["equilibrate_max_iter_1"] = 1                # maximal number of iterations without radial force; set to 1
$env["equilibrate_png_iter"] = 1                  # png plotting interval
$env["equilibrate_png_quantity"] = "stress"       # quantity to plot
$env["equilibrate_png_min_value"] = 0.0
$env["equilibrate_png_max_value"] = 0.01

# Parameters used by stent deployment code
$env["deploy_max_run_time_1"] = 3000              # original setting had fixed 2000
$env["deploy_convergence_limit_1"] = 1e-5
$env["deploy_max_iter_2"] = 2                     # number of iterations after deployment
$env["deploy_max_run_time_2"] = 5000              # original setting had fixed 2000
$env["deploy_convergence_limit_2"] = 1e-6
$env["deploy_png_iter"] = 1                       # png plotting interval
$env["deploy_png_quantity"] = "stress"            # quantity to plot
$env["deploy_png_min_value"] = 0.0
$env["deploy_png_max_value"] = 0.01
