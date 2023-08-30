# URDF Compose

URDF Compose is a package for dynamically composing urdfs in Python.

Often, robotics codebases will need to be written to deal with a whole host of combinations of hardware. For instance, say a codebase deals with robots that are built of a robot arm and a gripper. And say the system is built to deal with have 2 types of robot arms, and 5 types of grippers. In order to do this, one needs a different URDF for each of the 10 possible combinations. Traditionally, this would likely be done either by creating a seperate URDF by hand for each combination, or by creating a seperate XACRO for each one.

This package provides another solution by allowing one to dynamically compose urdfs using Python code. That way, one only need to create a urdf per component, and doesn't have to do exponentially more work with more components.

## Usage

### Simple Rod Example

The following example illustrates how to use this package to create a urdf of a number of rods connected in a chain.

In order to combine the urdfs, each component urdf needs links to represent "inputs" and "outputs". Simply put, "inputs" are spots on the component where it can connect to the rest of the urdf, and "outputs" are where other urdfs can be connected to it.

Below is a urdf we can use for creating this chain of rods:

```urdf
<?xml version="1.0" encoding="utf-8"?>
<robot name="rod">
    <link name="INPUT-rod">
        <inertial>
            <origin xyz="0 0 0" rpy="0 0 0" />
            <mass value="1.0" />
            <inertia ixx="1E-04" ixy="0" ixz="0" iyy="1E-04" iyz="0" izz="1E-05" />
        </inertial>
    </link>
    <link name="OUTPUT-rod"/>
    <joint name="joint" type="fixed">
        <origin xyz="0 0 0.05" rpy="0 0 0" />
        <parent link="INPUT-rod" />
        <child link="OUTPUT-rod" />
        <axis xyz="0 0 0" />
    </joint>
</robot>
```

Notice the names of input and output links start with "INPUT" and "OUTPUT" respectivelly. This indicates that they are the default input and output links. If they were lowercase, it would indicate they are inputs and outputs, but you would need to explictly indicate what input or otuput you want to use.

Let's look at basic code for creating a new urdf composed of two rods:

```python
from urdf_compose import ExplicitURDFObj, sequence,
ROD_PATH = ...
ROD_PAIR_PATH = ...
# Create an object referencing the original file, and checks the urdf to make sure its valid
extender_urdf = ExplicitURDFObj(ROD_PATH)
# Basic construct for making a sequence of n urdfs, each connected to the previous
composed_urdf = sequence(extender_urdf, extender_urdf)
write_and_check_urdf(composed_urdf, ROD_PAIR_PATH) # Checks the urdf is valid, and writes the urdf to the file
```

You can see this example in `examples/simple_chain/make_chain.py`. It will output a urdf with:
- both of the extender urdfs
- appropriate links and joints renamed as to prevent name collisions
- a dummy joint (fixed, with 0 origin and axis), that connects the two urdfs.

As a result of these requirments, the output becomes very hard for a human to read. Nonehteless, let's take a look at it:

```urdf
<?xml version='1.0' encoding='UTF-8'?>
<robot name="vgc10_link">
    <link name="INPUT-link">
        <inertial>
            <origin xyz="-1.14523654741374E-09 -2.79672501268441E-08 0.0228788479998501" rpy="0 0 0" />
            <mass value="0.00550575237578726" />
            <inertia ixx="1.33005016450342E-06" ixy="-5.64140714952826E-13" ixz="2.57434879543699E-14" iyy="1.33986100736006E-06" iyz="2.43974888325099E-13" izz="1.66618922257867E-07" />
        </inertial>
    </link>
    <link name="CONNECTED:OUTPUT-link"><inertial>
        <origin xyz="0 0 0" rpy="0 0 0" />
        <mass value="0" />
        <inertia ixx="0" ixy="0" ixz="0" iyy="0" iyz="0" izz="0" />
    </inertial></link>
    <joint name="joint" type="fixed">
        <origin xyz="0 0 0.05" rpy="0 0 0" />
        <parent link="INPUT-link" />
        <child link="CONNECTED:OUTPUT-link" />
        <axis xyz="0 0 0" />
    </joint>
<joint name="GENERATED_CONNECTION" type="fixed">
    <origin xyz="0 0 0" rpy="0 0 0" />
    <parent link="CONNECTED:OUTPUT-link" />
    <child link="CONNECTED:INPUT-link" />
    <axis xyz="0 0 0" />
</joint><link name="CONNECTED:INPUT-link">
        <inertial>
            <origin xyz="-1.14523654741374E-09 -2.79672501268441E-08 0.0228788479998501" rpy="0 0 0" />
            <mass value="0.00550575237578726" />
            <inertia ixx="1.33005016450342E-06" ixy="-5.64140714952826E-13" ixz="2.57434879543699E-14" iyy="1.33986100736006E-06" iyz="2.43974888325099E-13" izz="1.66618922257867E-07" />
        </inertial>
    </link>
    <link name="OUTPUT-link"><inertial>
        <origin xyz="0 0 0" rpy="0 0 0" />
        <mass value="0" />
        <inertia ixx="0" ixy="0" ixz="0" iyy="0" iyz="0" izz="0" />
    </inertial></link>
    <joint name="joint(1)" type="fixed">
        <origin xyz="0 0 0.05" rpy="0 0 0" />
        <parent link="CONNECTED:INPUT-link" />
        <child link="OUTPUT-link" />
        <axis xyz="0 0 0" />
    </joint>
</robot>
```

Notice the:
- `GENERATED_CONNECTION` joint
- The used output and input links get the literal `CONNECTED` appended to the start of its name

With these renames, one might want to know the new name of a link or joint. The following example shows how to find what "joint" in the second of the urdfs gets renamed to:

```python
extender_urdf1 = ExplicitURDFObj(ROD_PATH)
extender_urdf2 = ExplicitURDFObj(ROD_PATH) # Note: we have two seperate objects. Reasoning is explained later.
composed_urdf = sequence(extender_urdf1, extender_urdf2)

name_map = composed_urdf.name_map.collapse({extender_urdf2}) # Get an object that allows us to lookup new names for the given urdfs
print(name_map.lookup(extender_urdf2, "joint")) # prints "joint(1)"
```

Note that we have to create this object out of seperate urdf objects, even though they are from the same file. If we didn't, the name map wouldn't be able to distinguish between the first and second urdf. To illustrate this, we have the following example:

```python
extender_urdf = ExplicitURDFObj(ROD_PATH)
composed_urdf = sequence(extender_urdf, extender_urdf)

name_map = composed_urdf.name_map.collapse_safe({extender_urdf2}) # Using "collapse_safe" so that it returns the error
print(name_map) # prints a "RepeatedURDFError" object
```

### Branching Connection Example

The following example illustrates how we can create a composed urdf where one component has two outputs.

We now introduce the following urdf, that is like the original rod, except it has an extra output half way down the rod, faced sideways:
```urdf
<?xml version="1.0" encoding="utf-8"?>
<robot name="v_rod">
    <link name="INPUT-rod">
        <inertial>
            <origin xyz="0 0 0" rpy="0 0 0" />
            <mass value="1.0" />
            <inertia ixx="1E-04" ixy="0" ixz="0" iyy="1E-04" iyz="0" izz="1E-05" />
        </inertial>
    </link>
    <link name="OUTPUT-straight_output"/>
    <link name="output-sideways_output"/>
    <joint name="joint_straight" type="fixed">
        <origin xyz="0 0 0.05" rpy="0 0 0" />
        <parent link="INPUT-rod" />
        <child link="OUTPUT-straight_output" />
        <axis xyz="0 0 0" />
    </joint>
    <joint name="joint_sideways" type="fixed">
        <origin xyz="0 0.05 0.025" rpy="0 0 1.57" />
        <parent link="INPUT-rod" />
        <child link="output-sideways_output" />
        <axis xyz="0 0 0" />
    </joint>
</robot>
```

The following code shows how we can connect this urdf to two other rods:

```python
V_ROD_PATH = ...
SIMPLE_BRANCHED_CHAIN = ...

rod_urdf1 = ExplicitURDFObj(ROD_PATH)
rod_urdf2 = ExplicitURDFObj(ROD_PATH)
v_rod_urdf = ExplicitURDFObj(V_ROD_PATH)
simple_branched_chain = branch(
    v_rod_urdf,
    [
        rod_urdf1,
        # Note that we have to specify which output the second rod is using, b/c
        #   it is not connected to the default output
        (rod_urdf2, URDFConn("sideways_output"))
    ]
)
write_and_check_urdf(simple_branched_chain, SIMPLE_BRANCHED_CHAIN)
```

In addition, we can combine a branch and a sequence in order to attach a rod to the input of the v rod.

```python
rod_urdf3 = ExplicitURDFObj(ROD_PATH)
full_chain = sequence(
    rod_urdf3,
    branch=simple_branched_chain
)
```
Note that in this example, simple_branched_chain is passed as the `branch` kwarg rather than another one of the children because the children must be `URDFObj`s, not `URDFTree`s. This allows us to ensure that rod_urdf3 will be connected to `v_rod_urdf`, not `rod_urdf` or `rod_urdf2`. If we wanted to connect the simple_branched_chain first, we could pass it as another child to sequence, but we would then not have the same guarantee about which urdf it connects to:

```python
full_chain = sequence(
    rod_urdf3,
    simple_branched_connected
)
```
