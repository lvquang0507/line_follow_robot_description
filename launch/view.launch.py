from launch import LaunchDescription
from launch.substitutions import (
    Command,
    FindExecutable,
    PathJoinSubstitution,
    LaunchConfiguration,
)
from launch.actions import DeclareLaunchArgument
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    pkg_name = "line_follow_robot_description"

    use_sim_time = LaunchConfiguration("use_sim_time")

    # Get URDF via xacro
    robot_description_content = Command(
        [
            PathJoinSubstitution([FindExecutable(name="xacro")]),
            " ",
            PathJoinSubstitution(
                [
                    FindPackageShare(pkg_name),
                    "urdf",
                    "line_follow_robot.urdf.xacro",
                ]
            ),
        ]
    )

    params = {
        "robot_description": robot_description_content,
        "use_sim_time": use_sim_time,
    }

    # rviz_config_file = PathJoinSubstitution(
    #     [
    #         FindPackageShare(description_package),
    #         "rviz",
    #         "gantry_type_welding_robot.rviz",
    #     ]
    # )

    joint_state_publisher_node = Node(
        package="joint_state_publisher_gui",
        executable="joint_state_publisher_gui",
    )
    robot_state_publisher_node = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        output="both",
        parameters=[params],
    )
    rviz_node = Node(
        package="rviz2",
        executable="rviz2",
        name="rviz2",
        output="log",
        # arguments=["-d", rviz_config_file],
    )

    return LaunchDescription(
        [
            DeclareLaunchArgument(
                "use_sim_time",
                default_value="false",
                description="use simulation time if set to true",
            ),
            joint_state_publisher_node,
            robot_state_publisher_node,
            rviz_node,
        ]
    )
