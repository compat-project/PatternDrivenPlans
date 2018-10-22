# Check. Muscle environment is loaded
abort "Run 'source [MUSCLE_HOME]/etc/muscle.profile' before this script" if not ENV.has_key?('MUSCLE_HOME')

# Path to the binaries of the models to be coupled
dir = ENV["MUSCLE_KERNELS_DIR"]

PROFILE = true
DEBUG_ALLINEA = false

small = MPIInstance.new('small', "#{dir}/tube_muscle2_small") #{:mpiexec_args => '-np 2'}
small2 = MPIInstance.new('small2', "#{dir}/tube_muscle2_small2")#{:mpiexec_args => '-np 2'}
large = MPIInstance.new('large', "#{dir}/tube_muscle2_large")#{:mpiexec_args => '-np 4'}

if PROFILE
  small['mpiexec_command']='map_kernel'
  small['mpiexec_args']='--profile mpiexec -np '+ENV["QCG_KERNEL_small"]

  small2['mpiexec_command']='map_kernel'
  small2['mpiexec_args']='--profile mpiexec -np '+ENV["QCG_KERNEL_small2"]

  large['mpiexec_command']='map_kernel'
  large['mpiexec_args']='--profile mpiexec -np '+ENV["QCG_KERNEL_large"]
elsif DEBUG_ALLINEA
  small['mpiexec_command']='ddt'
  small['mpiexec_args']='--offline mpiexec -np '+ENV["QCG_KERNEL_small"]

  small2['mpiexec_command']='ddt'
  small2['mpiexec_args']='--offline mpiexec -np '+ENV["QCG_KERNEL_small2"]

  large['mpiexec_command']='ddt'
  large['mpiexec_args']='--offline mpiexec -np '+ENV["QCG_KERNEL_large"]
else
  small['mpiexec_command']='mpiexec'
  small['mpiexec_args']='-np '+ENV["QCG_KERNEL_small"]

  small2['mpiexec_command']='mpiexec'
  small2['mpiexec_args']='-np '+ENV["QCG_KERNEL_small2"]

  large['mpiexec_command']='mpiexec'
  large['mpiexec_args']='-np '+ENV["QCG_KERNEL_large"]
end

$env['repeat'] = 1 #2
$env['large:collisions']= 2 #00
$env['small:collisions']= 1 #40
$env['small2:collisions']= 1 #40 #remember you have a serial part witch is collisions/2
# configure connection scheme
small.couple(large, 'out' => 'in')
large.couple(small, 'out' => 'in')

small2.couple(large, 'out2' => 'in2')
large.couple(small2, 'out2' => 'in2')
