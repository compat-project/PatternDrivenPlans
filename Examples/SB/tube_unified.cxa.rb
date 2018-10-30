################################################################################
###   configuration file for a MUSCLE CxA                                    ###
################################################################################
abort "this is a configuration file to be used with the MUSCLE bootstrap utility" if __FILE__ == $0

KDIR = ENV["MUSCLE_KERNELS_DIR"]
INPUTDIR = ENV["INPUT_DIR"]



K_large01 = ENV["QCG_KERNEL_large01"]
K_small = ENV["QCG_KERNEL_small"]
K_small2 = ENV["QCG_KERNEL_small2"]

################################################################################
#     WORKFLOW LOGIC OPTIONS                                                   #
################################################################################
PROFILE      = true
DEBUG_ALLINEA = false


# Define steps, input files, cxa properties, commands and parameters 
# You can do this using cxa.env['property']=value
#cxa = Cxa.LAST


#if PROFILE
#  large= NativeInstance.new('large01','map', args: "--profile mpiexec -np  #{K_large01} #{KDIR}/tube_muscle2_large")
#  small1= NativeInstance.new('small1','map', args: "--profile mpiexec -np  #{K_small1} #{KDIR}/tube_muscle2_small1")
#  small2= NativeInstance.new('small2','map', args: "--profile mpiexec -np  #{K_small2} #{KDIR}/tube_muscle2_small2")
#else 
#  if DEBUG_ALLINEA
#    DEBUG_ALLINEA=false
#  else
#    large= MPIInstance.new('large01', "#{KDIR}/tube_muscle2_large",  mpiexec_args: "-np #{K_large01}")
#    small1= MPIInstance.new('small1', "#{KDIR}/tube_muscle2_small",  mpiexec_args: "-np #{K_small1}")
#    small2= MPIInstance.new('small2', "#{KDIR}/tube_muscle2_small2", mpiexec_args: "-np #{K_small2}")
#  end
#end


small = MPIInstance.new('small', "#{KDIR}/tube_muscle2_small") 
small2 = MPIInstance.new('small2', "#{KDIR}/tube_muscle2_small2")
large = MPIInstance.new('large', "#{KDIR}/tube_muscle2_large")

if PROFILE
  small['mpiexec_command']='map_kernel'
  small['mpiexec_args']='--profile mpiexec -np '+ K_small

  small2['mpiexec_command']='map_kernel'
  small2['mpiexec_args']='--profile mpiexec -np '+ K_small2 

  large['mpiexec_command']='map_kernel'
  large['mpiexec_args']='--profile mpiexec -np '+ K_large01
elsif DEBUG_ALLINEA
  small['mpiexec_command']='ddt'
  small['mpiexec_args']='--offline mpiexec -np '+ K_small

  small2['mpiexec_command']='ddt'
  small2['mpiexec_args']='--offline mpiexec -np '+ K_small2 

  large['mpiexec_command']='ddt'
  large['mpiexec_args']='--offline mpiexec -np '+ K_large01
else
  small['mpiexec_command']='mpiexec'
  small['mpiexec_args']='-np '+ K_small

  small2['mpiexec_command']='mpiexec'
  small2['mpiexec_args']='-np '+ K_small2 

  large['mpiexec_command']='mpiexec'
  large['mpiexec_args']='-np '+ K_large01
end


#$env["large01:mpiexec_command"] = "mpiexec"
#$env["small:mpiexec_command"] = "mpiexec"
#$env["small2:mpiexec_command"] = "mpiexec"

$env["large01:dt"]= "1s"
$env["default_dt"]= "1s"
$env["large01:T"] = "1s" 
$env["max_timesteps"]= "1s"
$env["small:dt"]= "1s"
$env["default_dt"] = "1s"
$env["small2:dt"]= "1s"
$env["default_dt"] = "1s"
$env["small2:T"]= "1s"
$env["max_timesteps"] = "1s"
$env["small:T"]= "1s" 
$env["max_timesteps"] = "1s"

$env["INPUT"]= INPUTDIR

$env['repeat'] = 20 #2
$env['large:collisions']= 80 #00
$env['small:collisions']= 40 #40
$env['small2:collisions']= 20 #40 #remember you have a serial part witch is collisions/2


# configure connection scheme

small.couple(large, 'out' => 'in')
large.couple(small, 'out' => 'in')

small2.couple(large, 'out2' => 'in2')
large.couple(small2, 'out2' => 'in2')
