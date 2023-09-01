# Introducing URDF Compose: A Package for dynamic composition of URDFs

Here at Tutor Intelligence, we produce a highly configurable robotic system. For us, using a couple of kinds of robot arms, a few types of cameras, and a handful of grippers, means we have more than a thousand configurations to support. This introduces a major issue in constructing URDFs, the XML based language for specifying robot models.

Traditionally, for every physically distinct robotic system, you need to create a new URDF by hand. For a highly configurable system like ours, creating each URDF by hand would be nearly impossible. There are tools out there to make it easier, but we found them all insufficient once you get any reasonable amount of configuration.

So we built URDF Compose, a package that allows you to dynamically build up URDFs in Python. The approach is fairly straightforward: you first mark links on the component urdfs as inputs or outputs, and then you can use URDF Compose to connect the output of one urdf to the input of another urdf. In tandom with intelligent error checking, it provides a powerful framework for creating URDFs more rubstly without any exponential cost.

If you want to follow along, you can install by running `pip install urdf-compose` and [installing check_urdf](https://command-not-found.com/check_urdf)

### Using URDF Compose

The first step to use URDF Compose is to mark the input and output links on the URDFs of the components that will make up your robot. Simply stick “INPUT:” or “OUTPUT:” at the start of the names of the links you want to mark. Note that upper case means its the default link–if you need multiple inputs or outputs, use lower cases. You can find some examples [here](https://github.com/tutorintelligence/urdf-compose#simple-rod-example).

Once you have your urdfs, the protocol for connecting them is simple.
```python
from urdf_compose import ExplicitURDFObj, sequence
urdf1 = ExplicitURDFObj(PATH_TO_SOME_URDF1)
urdf2 = ExplicitURDFObj(PATH_TO_SOME_URDF2)
very_simple_connected_urdf = sequence(urdf1, urdf2)
```
The above example will connect the default output link on urdf1 to the default input link on urdf2. [You can also use a non-default input or output](https://github.com/tutorintelligence/urdf-compose/blob/main/README.md#non-default-inputs-or-outputs).

The `branch` function then allows you to connect many urdfs to the same base urdf. Say you had three urdfs you want to connect. You could use `sequence`, which would connect the third urdf to the second urdf, and the second urdf to the first urdf. Or you could use `branch`, which would connect both the second and third urdfs directly to the first urdf:
```python
from urdf_compose import ExplicitURDFObj, sequence
urdf3 = ExplicitURDFObj(PATH_TO_SOME_URDF3)
triple_sequence = sequence(urdf1, [urdf2, urdf3])
triple_branch = branch(urdf1, [urdf2, urdf3])
```

You can then use the output of `sequence` or `branch` just like any other urdf. So one could do:
```python
big_sequence = sequence(triple_sequence, triple_branch)
```

### Verification and Error Handling

Dealing with URDFs is a pain. A major benefit of moving the composition of urdfs to code is it allows better and more systematic error checking.

Both on loading and saving of urdfs, URDF Compose runs `check_urdf`. `check_urdf` is provided by [urdfdom tools](https://command-not-found.com/check_urdf), and gives a very helpful debugging message if for whatever reason your URDF isn’t valid. Automatically checking the component urdfs provides a major source of robustness, as finding issues in the larger final composed urdf is much harder.

When URDF Compose cannot connect to urdfs, it provides an informative message, as well as the offending URDF objects. Without these objects, that themselves are likely composed and hence don’t exist anywhere else, any issues at the connection step would be opaque.

### Some Drawbacks

The major drawback is the time it takes to update component urdfs with the correct input/output format. It's not too time instensive, but it's not negligble. We have internal tooling to make URDF Compose compaitable URDFs from Solidworks, and we hope to open source it in the not too distant future.

The other smaller drawback to think about is that as a result of the dummy joints, and some automatic renaming that has to happen on name collisions, the final urdfs can be harder to read. Generally, reading the final urdf isn’t such a critical operation, but if it does happen to matter a lot to you, this could be a loss.

—------------------------------------------------------------------------------------------------------------------

We welcome you to give this package a try and see if it helps you out! We’re excited to be seeing the field of robotics evolve, and hope that this can be another step on the road to more configurable, general, impactful robots. And of course, we will greatly appreciate any thoughts or issues on the [github repository](https://github.com/tutorintelligence/urdf-compose), where you can also get more usage details.
