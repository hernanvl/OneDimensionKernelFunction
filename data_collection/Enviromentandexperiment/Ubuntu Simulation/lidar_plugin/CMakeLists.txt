cmake_minimum_required(VERSION 3.0)
project(lidar_plugin)

find_package(gazebo REQUIRED)

include_directories(${GAZEBO_INCLUDE_DIRS})
link_directories(${GAZEBO_LIBRARY_DIRS})

add_library(lidar_plugin SHARED lidar_plugin.cpp)
target_link_libraries(lidar_plugin ${GAZEBO_LIBRARIES})
