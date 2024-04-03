if [ $# -eq 0 ]; then 
  echo "Give a file path to a urdf file."
else
  roslaunch urdf_tutorial display.launch model:=$1
fi
