import React from 'react';
import {
  Card,
  Row,
  Col,
  Statistic,
  Typography,
  Table,
  Tag,
  Progress,
  List,
  Avatar,
  Space,
  Button,
  Alert,
} from 'antd';
import {
  DatabaseOutlined,
  FileTextOutlined,
  CodeOutlined,
  BarChartOutlined,
  TrophyOutlined,
  ClockCircleOutlined,
  UserOutlined,
  ArrowUpOutlined,
  ArrowDownOutlined,
} from '@ant-design/icons';
import { useQuery } from '@tanstack/react-query';
import { analyticsApi, metadataApi } from '../services/api';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import dayjs from 'dayjs';

const { Title, Text } = Typography;

const DashboardPage: React.FC = () => {
  // Fetch dashboard data
  const { data: dashboardData, isLoading: dashboardLoading } = useQuery({
    queryKey: ['dashboard'],
    queryFn: analyticsApi.getDashboard,
    refetchInterval: 30000, // Refresh every 30 seconds
  });

  // Fetch recent metadata
  const { data: recentMetadata } = useQuery({
    queryKey: ['metadata', { page: 1, size: 5, sort_by: 'updated_at', sort_order: 'desc' }],
    queryFn: () => metadataApi.getMetadata({ page: 1, size: 5, sort_by: 'updated_at', sort_order: 'desc' }),
  });

  // Mock data for charts (replace with real data from API)
  const weeklyActivityData = [
    { name: 'Mon', metadata: 4, lookml: 2 },
    { name: 'Tue', metadata: 6, lookml: 3 },
    { name: 'Wed', metadata: 8, lookml: 4 },
    { name: 'Thu', metadata: 5, lookml: 2 },
    { name: 'Fri', metadata: 9, lookml: 5 },
    { name: 'Sat', metadata: 3, lookml: 1 },
    { name: 'Sun', metadata: 2, lookml: 1 },
  ];

  const qualityDistribution = [
    { name: 'Excellent (80-100%)', value: 35, color: '#52c41a' },
    { name: 'Good (60-79%)', value: 25, color: '#1890ff' },
    { name: 'Fair (40-59%)', value: 20, color: '#fa8c16' },
    { name: 'Poor (0-39%)', value: 10, color: '#f5222d' },
    { name: 'Not Rated', value: 10, color: '#d9d9d9' },
  ];

  const recentActivity = [
    {
      id: 1,
      type: 'metadata',
      title: 'Generated metadata for users table',
      user: 'John Doe',
      time: '2 minutes ago',
      status: 'completed',
    },
    {
      id: 2,
      type: 'lookml',
      title: 'Created LookML model for sales_transactions',
      user: 'Jane Smith',
      time: '15 minutes ago',
      status: 'completed',
    },
    {
      id: 3,
      type: 'metadata',
      title: 'Updated metadata for products table',
      user: 'Mike Johnson',
      time: '1 hour ago',
      status: 'completed',
    },
    {
      id: 4,
      type: 'database',
      title: 'Connected new PostgreSQL database',
      user: 'Sarah Wilson',
      time: '2 hours ago',
      status: 'completed',
    },
    {
      id: 5,
      type: 'metadata',
      title: 'Metadata generation failed for large_table',
      user: 'System',
      time: '3 hours ago',
      status: 'failed',
    },
  ];

  const getActivityIcon = (type: string) => {
    switch (type) {
      case 'metadata':
        return <FileTextOutlined style={{ color: '#1890ff' }} />;
      case 'lookml':
        return <CodeOutlined style={{ color: '#52c41a' }} />;
      case 'database':
        return <DatabaseOutlined style={{ color: '#fa8c16' }} />;
      default:
        return <ClockCircleOutlined style={{ color: '#666' }} />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'success';
      case 'failed':
        return 'error';
      case 'pending':
        return 'processing';
      default:
        return 'default';
    }
  };

  return (
    <div style={{ padding: 24 }}>
      <div style={{ marginBottom: 24 }}>
        <Title level={2}>
          <BarChartOutlined style={{ marginRight: 8, color: '#1890ff' }} />
          Dashboard
        </Title>
        <Text type="secondary">
          Welcome back! Here's what's happening with your metadata projects.
        </Text>
      </div>

      {/* Key Metrics */}
      <Row gutter={[24, 24]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Total Databases"
              value={dashboardData?.total_databases || 8}
              prefix={<DatabaseOutlined style={{ color: '#1890ff' }} />}
              suffix={
                <div style={{ fontSize: 12, color: '#52c41a' }}>
                  <ArrowUpOutlined /> 12%
                </div>
              }
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Table Metadata"
              value={dashboardData?.total_metadata || 156}
              prefix={<FileTextOutlined style={{ color: '#52c41a' }} />}
              suffix={
                <div style={{ fontSize: 12, color: '#52c41a' }}>
                  <ArrowUpOutlined /> 24%
                </div>
              }
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="LookML Models"
              value={dashboardData?.total_lookml_models || 42}
              prefix={<CodeOutlined style={{ color: '#fa8c16' }} />}
              suffix={
                <div style={{ fontSize: 12, color: '#52c41a' }}>
                  <ArrowUpOutlined /> 8%
                </div>
              }
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Avg. Quality Score"
              value={87}
              prefix={<TrophyOutlined style={{ color: '#722ed1' }} />}
              suffix="%"
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
      </Row>

      <Row gutter={[24, 24]}>
        {/* Activity Chart */}
        <Col xs={24} lg={16}>
          <Card title="Weekly Activity" style={{ height: 400 }}>
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={weeklyActivityData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip />
                <Line
                  type="monotone"
                  dataKey="metadata"
                  stroke="#1890ff"
                  strokeWidth={2}
                  name="Metadata Generated"
                />
                <Line
                  type="monotone"
                  dataKey="lookml"
                  stroke="#52c41a"
                  strokeWidth={2}
                  name="LookML Models"
                />
              </LineChart>
            </ResponsiveContainer>
          </Card>
        </Col>

        {/* Data Quality Distribution */}
        <Col xs={24} lg={8}>
          <Card title="Data Quality Distribution" style={{ height: 400 }}>
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={qualityDistribution}
                  cx="50%"
                  cy="50%"
                  innerRadius={40}
                  outerRadius={80}
                  paddingAngle={5}
                  dataKey="value"
                >
                  {qualityDistribution.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip formatter={(value) => [`${value}%`, 'Tables']} />
              </PieChart>
            </ResponsiveContainer>
            <div style={{ marginTop: 16 }}>
              {qualityDistribution.map((item, index) => (
                <div key={index} style={{ display: 'flex', alignItems: 'center', marginBottom: 8 }}>
                  <div
                    style={{
                      width: 12,
                      height: 12,
                      backgroundColor: item.color,
                      marginRight: 8,
                      borderRadius: 2,
                    }}
                  />
                  <Text style={{ fontSize: 12 }}>{item.name}: {item.value}%</Text>
                </div>
              ))}
            </div>
          </Card>
        </Col>
      </Row>

      <Row gutter={[24, 24]} style={{ marginTop: 24 }}>
        {/* Recent Metadata */}
        <Col xs={24} lg={12}>
          <Card
            title="Recent Metadata"
            extra={
              <Button type="link" size="small">
                View All
              </Button>
            }
          >
            {recentMetadata?.items.length ? (
              <Table
                dataSource={recentMetadata.items.slice(0, 5)}
                pagination={false}
                size="small"
                columns={[
                  {
                    title: 'Table',
                    key: 'table',
                    render: (_, record) => (
                      <div>
                        <Text strong>{record.table_name}</Text>
                        <br />
                        <Text type="secondary" style={{ fontSize: 12 }}>
                          {record.database_name}.{record.schema_name}
                        </Text>
                      </div>
                    ),
                  },
                  {
                    title: 'Quality',
                    dataIndex: 'data_quality_score',
                    key: 'quality',
                    render: (score: number) => (
                      <Progress
                        type="circle"
                        size={32}
                        percent={score || 0}
                        format={(percent) => `${percent}%`}
                      />
                    ),
                  },
                  {
                    title: 'Type',
                    dataIndex: 'generated_by',
                    key: 'type',
                    render: (type: string) => (
                      <Tag color={type === 'llm' ? 'blue' : type === 'manual' ? 'green' : 'purple'}>
                        {type.toUpperCase()}
                      </Tag>
                    ),
                  },
                  {
                    title: 'Updated',
                    dataIndex: 'updated_at',
                    key: 'updated',
                    render: (date: string) => (
                      <Text style={{ fontSize: 12 }}>
                        {dayjs(date).fromNow()}
                      </Text>
                    ),
                  },
                ]}
              />
            ) : (
              <div style={{ textAlign: 'center', padding: '24px 0' }}>
                <FileTextOutlined style={{ fontSize: 48, color: '#d9d9d9', marginBottom: 16 }} />
                <div>
                  <Text type="secondary">No metadata generated yet</Text>
                  <br />
                  <Button type="primary" style={{ marginTop: 8 }}>
                    Generate Your First Metadata
                  </Button>
                </div>
              </div>
            )}
          </Card>
        </Col>

        {/* Recent Activity */}
        <Col xs={24} lg={12}>
          <Card
            title="Recent Activity"
            extra={
              <Button type="link" size="small">
                View All
              </Button>
            }
          >
            <List
              dataSource={recentActivity}
              renderItem={(item) => (
                <List.Item key={item.id}>
                  <List.Item.Meta
                    avatar={
                      <Avatar
                        size="small"
                        icon={getActivityIcon(item.type)}
                        style={{
                          backgroundColor:
                            item.status === 'failed' ? '#ff4d4f' : '#f0f0f0',
                        }}
                      />
                    }
                    title={
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <Text style={{ fontSize: 14 }}>{item.title}</Text>
                        <Tag color={getStatusColor(item.status)} size="small">
                          {item.status}
                        </Tag>
                      </div>
                    }
                    description={
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <Text type="secondary" style={{ fontSize: 12 }}>
                          by {item.user}
                        </Text>
                        <Text type="secondary" style={{ fontSize: 12 }}>
                          {item.time}
                        </Text>
                      </div>
                    }
                  />
                </List.Item>
              )}
            />
          </Card>
        </Col>
      </Row>

      {/* System Health Alert */}
      <Row style={{ marginTop: 24 }}>
        <Col span={24}>
          <Alert
            message="System Status: All services operational"
            description="API server, database connections, and background jobs are running normally. Last health check: 2 minutes ago."
            type="success"
            showIcon
            action={
              <Button size="small" type="link">
                View Details
              </Button>
            }
          />
        </Col>
      </Row>
    </div>
  );
};

export default DashboardPage; 