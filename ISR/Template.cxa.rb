
# Check Muscle environment is loaded
abort "Run 'source [MUSCLE_HOME]/etc/muscle.profile' before this script" if not ENV.has_key?('MUSCLE_HOME')

 
# Define steps, input files, cxa properties, commands and parameters 
# You can do this using cxa.env['property']=value
cxa = Cxa.LAST
 
# Declare kernels
cxa.add_kernel('SMC', 'muscle.core.standalone.NativeKernel')
cxa.add_kernel('Blob', 'muscle.core.standalone.NativeKernel')
cxa.add_kernel('BF', 'muscle.core.standalone.MPIKernel')
cxa.add_kernel('DD', 'muscle.core.standalone.Kernel')
cxa.add_kernel('Voxel', 'muscle.core.kernel.DuplicationMapper')
cxa.add_kernel('Add', 'muscle.core.kernel.DuplicationMapper')
cxa.add_kernel('Out', 'muscle.core.kernel.DuplicationMapper')
cxa.add_kernel('In', 'muscle.core.kernel.DuplicationMapper')


# Configure connection schema
#In tie fill with the appropriate connection ports
# Notice that if a submodel connects with mapper, then one tie argument is needed only!!!
cs = cxa.cs
cs.attach('SMC' => 'Voxel') {
tie('   ', '   ')
}
cs.attach('Voxel' => 'Add') {
tie('   ', '   ')
}
cs.attach('Voxel' => 'Blob') {
tie('   ', '   ')
}
cs.attach('Voxel' => 'In') {
tie('   ', '   ')
}
cs.attach('Blob' => 'Add') {
tie('   ')
}
cs.attach('Add' => 'Out') {
tie('   ')
}
cs.attach('Out' => 'BF') {
tie('   ')
}
cs.attach('Out' => 'DD') {
tie('   ')
}
cs.attach('BF' => 'In') {
tie('   ', '   ')
}
cs.attach('DD' => 'In') {
tie('   ', '   ')
}
cs.attach('In' => 'SMC') {
tie('   ', '   ')
}


