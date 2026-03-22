#include <gazebo/gazebo.hh>
#include <gazebo/sensors/RaySensor.hh>
#include <gazebo/transport/transport.hh>
#include <gazebo/msgs/msgs.hh>
#include <fstream>
#include <sstream>

namespace gazebo {

class LidarPublisher : public SensorPlugin {
public:
  void Load(sensors::SensorPtr _sensor, sdf::ElementPtr _sdf) override {
    this->sensor = std::dynamic_pointer_cast<sensors::RaySensor>(_sensor);
    if (!this->sensor) { gzerr << "[LidarPlugin] No es RaySensor\n"; return; }

    this->node = transport::NodePtr(new transport::Node());
    this->node->Init();
    this->pub = this->node->Advertise<msgs::LaserScanStamped>(
      "/gazebo/cuarto_lidar/lidar_estatico/link/hokuyo/scan", 50);

    this->conn = this->sensor->ConnectUpdated(
      std::bind(&LidarPublisher::OnUpdate, this));
    this->sensor->SetActive(true);

    this->outputFile = "/tmp/lidar_scan.txt";
    gzmsg << "[LidarPlugin] Listo! Escribiendo en: " << this->outputFile << "\n";
  }

private:
  void OnUpdate() {
    std::vector<double> ranges;
    this->sensor->Ranges(ranges);
    if (ranges.empty()) return;

    // Publicar por transport
    msgs::LaserScanStamped msg;
    msgs::Set(msg.mutable_time(), this->sensor->LastUpdateTime());
    auto *scan = msg.mutable_scan();
    ignition::math::Pose3d pose = this->sensor->Pose();
    msgs::Set(scan->mutable_world_pose(), pose);
    scan->set_frame(this->sensor->Name());
    scan->set_angle_min(this->sensor->AngleMin().Radian());
    scan->set_angle_max(this->sensor->AngleMax().Radian());
    scan->set_angle_step(this->sensor->AngleResolution());
    scan->set_range_min(this->sensor->RangeMin());
    scan->set_range_max(this->sensor->RangeMax());
    scan->set_count(this->sensor->RayCount());
    scan->set_vertical_count(1);
    scan->set_vertical_angle_min(0);
    scan->set_vertical_angle_max(0);
    scan->set_vertical_angle_step(0);
    for (auto r : ranges) { scan->add_ranges(r); scan->add_intensities(0.0); }
    this->pub->Publish(msg);

    // ✅ TAMBIÉN escribir a archivo
    std::ofstream f(this->outputFile);
    f << "angle_min: " << this->sensor->AngleMin().Radian() << "\n";
    f << "angle_max: " << this->sensor->AngleMax().Radian() << "\n";
    f << "count: " << ranges.size() << "\n";
    for (auto r : ranges) f << r << "\n";
    f.close();

    this->scanCount++;
    if (this->scanCount % 50 == 0)
      gzmsg << "[LidarPlugin] Scan #" << this->scanCount 
            << " — " << ranges.size() << " puntos\n";
  }

  sensors::RaySensorPtr sensor;
  transport::NodePtr node;
  transport::PublisherPtr pub;
  event::ConnectionPtr conn;
  std::string outputFile;
  int scanCount = 0;
};

GZ_REGISTER_SENSOR_PLUGIN(LidarPublisher)

} // namespace gazebo
