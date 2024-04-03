# GGDL sample program
GGDL (Graph Grammar Definition Language) is an XML-based language to describe a graph grammar.
GGDL aims to be a unified description format for graph grammars and the preparation of the specification document is in progress.

This sample program generates URDF files of randomly constructed robots.
The construction rule for robots is based on Robogrammar [1].
The GGDL expression of Robogrammar is placed at `sample/RoboGrammar.grammar`.
 
## Requirement
* NetworkX 3.1~
* Matplotlib 3.7.4~

## Usage
Call `create_robot.sh` at the `sample` directory.
The URDF file of the generated robot is placed at `sample/generated_robots` as `tst.urdf`.

If ROS is available, `view_urdf.sh` launches rviz and shows the content of a URDF file.
### Example
`sh create_robot.sh`

`sh view_urdf.sh path/to/a/urdf/file.urdf`

## Reference
[1] Zhao et al.,  “Robogrammar: graph grammar for terrain-optimized robot design”, ACM Transactions on Graphics (TOG), 39(6), pp. 1-16, (2020).


