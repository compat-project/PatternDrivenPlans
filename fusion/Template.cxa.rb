
# Check Muscle environment is loaded
abort "Run 'source [MUSCLE_HOME]/etc/muscle.profile' before this script" if not ENV.has_key?('MUSCLE_HOME')

 
# Define steps, input files, cxa properties, commands and parameters 
# You can do this using cxa.env['property']=value
cxa = Cxa.LAST
 
# Declare kernels
cxa.add_kernel('init', 'muscle.core.standalone.NativeKernel')
cxa.add_kernel('transp', 'muscle.core.standalone.NativeKernel')
cxa.add_kernel('turb', 'muscle.core.standalone.MPIKernel')
cxa.add_kernel('equil', 'muscle.core.standalone.NativeKernel')
cxa.add_kernel('f2dv', 'muscle.core.standalone.NativeKernel')
cxa.add_kernel('dupEquil', 'muscle.core.kernel.DuplicationMapper')
cxa.add_kernel('dupCorep', 'muscle.core.kernel.DuplicationMapper')


# Configure connection schema
#In tie fill with the appropriate connection ports
# Notice that if a submodel connects with mapper, then one tie argument is needed only!!!
cs = cxa.cs
cs.attach('init' => 'transp') {
tie('   ', '   ')
tie('   ', '   ')
tie('   ', '   ')
tie('   ', '   ')
tie('   ', '   ')
tie('   ', '   ')
}
cs.attach('transp' => 'dupCorep') {
tie('   ', '   ')
}
cs.attach('transp' => 'equil') {
tie('   ', '   ')
}
cs.attach('dupCorep' => 'turb') {
tie('   ', '   ')
}
cs.attach('dupCorep' => 'f2dv') {
tie('   ', '   ')
}
cs.attach('dupCorep' => 'transp') {
tie('   ')
}
cs.attach('equil' => 'dupEquil') {
tie('   ')
}
cs.attach('dupEquil' => 'turb') {
tie('   ', '   ')
}
cs.attach('dupEquil' => 'f2dv') {
tie('   ', '   ')
}
cs.attach('dupEquil' => 'transp') {
tie('   ', '   ')
}
cs.attach('turb' => 'f2dv') {
tie('   ', '   ')
}
cs.attach('f2dv' => 'transp') {
tie('   ', '   ')
}


