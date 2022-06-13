from urdf_obj import URDFObj 
from urdf_compose import urdf_append, URDFConn

if __name__ == "__main__":
    num_extenders = 50
    connections = [(URDFObj("urdfs/extender.urdf"), URDFConn("extender", "fixed_extender")) for _ in range(num_extenders - 1)]
    extenders_urdf = urdf_append(URDFObj("urdfs/extender.urdf"), connections)
    extenders_urdf.write("urdfs/putTogether2.urdf")