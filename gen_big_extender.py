from urdf_obj import URDFObj 
from urdf_compose import urdf_append, Connection

if __name__ == "__main__":
    num_extenders = 50
    connections = [(URDFObj("urdfs/extender.urdf"), Connection("extender", "fixed_extender")) for _ in range(num_extenders - 1)]
    new_urdf = urdf_append(URDFObj("urdfs/extender.urdf"), connections)
    new_urdf.write("urdfs/putTogether2.urdf")