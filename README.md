About Patterns
=============
`patterns` software maps submodels to the required architecture to abstract this complexity from user. It [generates|submit] middleware files required.

Look how easy it is to use:

    module load compat/common/patterns/dev2
    ./PatternDrivenPlans matrix.xml multiscale.xml

    * To run fusion case (example)
	** ./PatternDrivenPlans fusion/matrix.xml fusion/multiscale.xml -H supermuc --reservation supermuc:srv03-ib.49.r --notification name@serv.com

    * To run MATERIALS case (example)
	** /PatternDrivenPlans Materials/matrix.xml Materials/multiscale.xml -nd nodeDescription.xml -M 3


Documentation
=============
Please see the `documentation` folder.


Contribute
=======
- Issue Tracker: 
- Source Code: 


Support
=======
If you are having issues, please let us know.Please use @ to cobtact us.


License
=======
GNU General Public License v3.0.
