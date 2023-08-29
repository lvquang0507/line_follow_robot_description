import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription

from launch.substitutions import (
    Command,
    FindExecutable,
    PathJoinSubstitution,
    LaunchConfiguration,
)

# from launch.substitutions import LaunchConfiguration
from launch.actions import (
    IncludeLaunchDescription,
    RegisterEventHandler,
    TimerAction,
    DeclareLaunchArgument,
    ExecuteProcess,
)
from launch.event_handlers import OnProcessExit, OnProcessStart
from launch.launch_description_sources import PythonLaunchDescriptionSource
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

    robot_state_publisher_node = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        output="both",
        parameters=[params],
    )

    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            [
                os.path.join(
                    get_package_share_directory("gazebo_ros"),
                    "launch",
                    "gazebo.launch.py",
                )
            ]
        ),
    )

    spawn_entity = Node(
        package="gazebo_ros",
        executable="spawn_entity.py",
        arguments=["-topic", "robot_description", "-entity", "anna"],
        output="screen",
    )

    joint_state_broadcaster_spawn = ExecuteProcess(
        cmd=[
            "ros2",
            "control",
            "load_controller",
            "--set-state",
            "active",
            "joint_state_broadcaster",
        ],
        output="screen",
        params={"use_sim_time": use_sim_time},
    )

    delay_JSB_after_gazebo = RegisterEventHandler(
        event_handler=OnProcessStart(
            target_action=spawn_entity,
            on_start=[joint_state_broadcaster_spawn],
        )
    )

    robot_controllers = ["diff_drive_base_controller"]
    robot_controller_spawners = []

    for controller in robot_controllers:
        robot_controller_spawners += [
            ExecuteProcess(
                cmd=[
                    "ros2",
                    "control",
                    "load_controller",
                    "--set-state",
                    "active",
                    controller,
                ],
                output="screen",
            )
        ]

    delay_controller_after_JSB = []

    for controller in robot_controller_spawners:
        delay_controller_after_JSB += [
            RegisterEventHandler(
                event_handler=OnProcessExit(
                    target_action=joint_state_broadcaster_spawn,
                    on_exit=[TimerAction(period=3.0, actions=[controller])],
                )
            )
        ]

    return LaunchDescription(
        [
            DeclareLaunchArgument(
                "use_sim_time",
                default_value="false",
                description="use simulation time if set to true",
            ),
            robot_state_publisher_node,
            gazebo,
            spawn_entity,
            delay_JSB_after_gazebo,
        ]
        + delay_controller_after_JSB
    )
