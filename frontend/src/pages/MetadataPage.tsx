import React, { useState, useEffect } from 'react';
import {
  Card,
  Table,
  Button,
  Input,
  Select,
  Space,
  Tag,
  Typography,
  Row,
  Col,
  Modal,
  message,
  Progress,
  Tooltip,
  Drawer,
  Descriptions,
  Badge,
  Empty,
  Dropdown,
  Popconfirm,
} from 'antd';
import type { ColumnsType, TableProps } from 'antd/es/table';
import {
  SearchOutlined,
  PlusOutlined,
  FilterOutlined,
  DownloadOutlined,
  EditOutlined,
  DeleteOutlined,
  EyeOutlined,
  ReloadOutlined,
  FileTextOutlined,
  DatabaseOutlined,
  CalendarOutlined,
  MoreOutlined,
} from '@ant-design/icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { metadataApi } from '../services/api';
import type { TableMetadata, SearchParams } from '../types';
import dayjs from 'dayjs';
import relativeTime from 'dayjs/plugin/relativeTime';

dayjs.extend(relativeTime);

const { Title, Text, Paragraph } = Typography;
const { Search } = Input;
const { Option } = Select;

const MetadataPage: React.FC = () => {
  const [searchParams, setSearchParams] = useState<SearchParams>({
    page: 1,
    size: 10,
    sort_by: 'updated_at',
    sort_order: 'desc',
  });
  const [selectedMetadata, setSelectedMetadata] = useState<TableMetadata | null>(null);
  const [detailsVisible, setDetailsVisible] = useState(false);
  const [filterVisible, setFilterVisible] = useState(false);

  const queryClient = useQueryClient();

  // Fetch metadata with pagination and search
  const {
    data: metadataResponse,
    isLoading,
    error,
    refetch,
  } = useQuery({
    queryKey: ['metadata', searchParams],
    queryFn: () => metadataApi.getMetadata(searchParams),
    keepPreviousData: true,
  });

  // Delete metadata mutation
  const deleteMetadataMutation = useMutation({
    mutationFn: metadataApi.deleteMetadata,
    onSuccess: () => {
      message.success('Metadata deleted successfully');
      queryClient.invalidateQueries(['metadata']);
    },
    onError: (error: any) => {
      message.error(`Failed to delete metadata: ${error.message}`);
    },
  });

  // Export metadata mutation
  const exportMetadataMutation = useMutation({
    mutationFn: ({ id, format }: { id: string; format: 'json' | 'yaml' }) =>
      metadataApi.exportMetadata(id, format),
    onSuccess: (blob, variables) => {
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `metadata.${variables.format}`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
      message.success('Metadata exported successfully');
    },
    onError: (error: any) => {
      message.error(`Failed to export metadata: ${error.message}`);
    },
  });

  const handleSearch = (value: string) => {
    setSearchParams({
      ...searchParams,
      query: value || undefined,
      page: 1,
    });
  };

  const handleTableChange: TableProps<TableMetadata>['onChange'] = (pagination, filters, sorter) => {
    const newParams = {
      ...searchParams,
      page: pagination.current || 1,
      size: pagination.pageSize || 10,
    };

    if (sorter && !Array.isArray(sorter) && sorter.order) {
      newParams.sort_by = sorter.field as string;
      newParams.sort_order = sorter.order === 'ascend' ? 'asc' : 'desc';
    }

    setSearchParams(newParams);
  };

  const handleViewDetails = (record: TableMetadata) => {
    setSelectedMetadata(record);
    setDetailsVisible(true);
  };

  const handleDelete = (id: string) => {
    deleteMetadataMutation.mutate(id);
  };

  const handleExport = (id: string, format: 'json' | 'yaml') => {
    exportMetadataMutation.mutate({ id, format });
  };

  const getQualityColor = (score?: number): string => {
    if (!score) return 'default';
    if (score >= 80) return 'green';
    if (score >= 60) return 'orange';
    return 'red';
  };

  const getGenerationTypeColor = (type: string): string => {
    switch (type) {
      case 'llm':
        return 'blue';
      case 'manual':
        return 'green';
      case 'hybrid':
        return 'purple';
      default:
        return 'default';
    }
  };

  const columns: ColumnsType<TableMetadata> = [
    {
      title: 'Table',
      key: 'table',
      render: (_, record) => (
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <DatabaseOutlined style={{ color: '#1890ff' }} />
            <Text strong>{record.table_name}</Text>
          </div>
          <Text type="secondary" style={{ fontSize: 12 }}>
            {record.database_name}.{record.schema_name}
          </Text>
        </div>
      ),
      sorter: true,
    },
    {
      title: 'Description',
      dataIndex: 'description',
      key: 'description',
      render: (description: string) => (
        <Paragraph
          ellipsis={{
            rows: 2,
            expandable: false,
          }}
          style={{ margin: 0, maxWidth: 300 }}
        >
          {description || <Text type="secondary">No description</Text>}
        </Paragraph>
      ),
    },
    {
      title: 'Columns',
      key: 'columns',
      render: (_, record) => (
        <div>
          <Text strong>{record.columns.length}</Text>
          <Text type="secondary"> columns</Text>
        </div>
      ),
    },
    {
      title: 'Data Quality',
      dataIndex: 'data_quality_score',
      key: 'data_quality_score',
      render: (score: number) => (
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <Progress
            type="circle"
            size={40}
            percent={score || 0}
            strokeColor={getQualityColor(score)}
            format={(percent) => `${percent}%`}
          />
          <Text type="secondary" style={{ fontSize: 12 }}>
            Quality Score
          </Text>
        </div>
      ),
      sorter: true,
    },
    {
      title: 'Generation Type',
      dataIndex: 'generated_by',
      key: 'generated_by',
      render: (type: string) => (
        <Tag color={getGenerationTypeColor(type)}>
          {type.toUpperCase()}
        </Tag>
      ),
      filters: [
        { text: 'Manual', value: 'manual' },
        { text: 'LLM', value: 'llm' },
        { text: 'Hybrid', value: 'hybrid' },
      ],
    },
    {
      title: 'Last Updated',
      dataIndex: 'updated_at',
      key: 'updated_at',
      render: (date: string) => (
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
            <CalendarOutlined style={{ color: '#666', fontSize: 12 }} />
            <Text style={{ fontSize: 12 }}>
              {dayjs(date).fromNow()}
            </Text>
          </div>
          <Text type="secondary" style={{ fontSize: 11 }}>
            {dayjs(date).format('MMM DD, YYYY')}
          </Text>
        </div>
      ),
      sorter: true,
    },
    {
      title: 'Actions',
      key: 'actions',
      fixed: 'right',
      width: 120,
      render: (_, record) => (
        <Dropdown
          menu={{
            items: [
              {
                key: 'view',
                label: 'View Details',
                icon: <EyeOutlined />,
                onClick: () => handleViewDetails(record),
              },
              {
                key: 'edit',
                label: 'Edit',
                icon: <EditOutlined />,
                onClick: () => {
                  // TODO: Navigate to edit page
                  message.info('Edit functionality coming soon');
                },
              },
              {
                type: 'divider',
              },
              {
                key: 'export-json',
                label: 'Export JSON',
                icon: <DownloadOutlined />,
                onClick: () => handleExport(record.id, 'json'),
              },
              {
                key: 'export-yaml',
                label: 'Export YAML',
                icon: <DownloadOutlined />,
                onClick: () => handleExport(record.id, 'yaml'),
              },
              {
                type: 'divider',
              },
              {
                key: 'delete',
                label: 'Delete',
                icon: <DeleteOutlined />,
                danger: true,
                onClick: () => {
                  Modal.confirm({
                    title: 'Delete Metadata',
                    content: `Are you sure you want to delete metadata for ${record.table_name}?`,
                    okText: 'Delete',
                    okType: 'danger',
                    onOk: () => handleDelete(record.id),
                  });
                },
              },
            ],
          }}
        >
          <Button icon={<MoreOutlined />} size="small" />
        </Dropdown>
      ),
    },
  ];

  return (
    <div style={{ padding: 24 }}>
      <Row gutter={[24, 24]}>
        <Col span={24}>
          <Card>
            <div
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                marginBottom: 24,
              }}
            >
              <div>
                <Title level={3} style={{ margin: 0 }}>
                  <FileTextOutlined style={{ marginRight: 8, color: '#1890ff' }} />
                  Table Metadata
                </Title>
                <Text type="secondary">
                  Manage and view all generated table metadata
                </Text>
              </div>
              <Space>
                <Button
                  icon={<ReloadOutlined />}
                  onClick={() => refetch()}
                  loading={isLoading}
                >
                  Refresh
                </Button>
                <Button
                  type="primary"
                  icon={<PlusOutlined />}
                  onClick={() => {
                    // TODO: Navigate to generation page
                    message.info('Navigate to metadata generation');
                  }}
                >
                  Generate Metadata
                </Button>
              </Space>
            </div>

            <div
              style={{
                display: 'flex',
                gap: 16,
                marginBottom: 24,
                flexWrap: 'wrap',
              }}
            >
              <Search
                placeholder="Search tables, databases, or descriptions..."
                allowClear
                onSearch={handleSearch}
                style={{ width: 300 }}
                enterButton={<SearchOutlined />}
              />
              <Button
                icon={<FilterOutlined />}
                onClick={() => setFilterVisible(true)}
              >
                Advanced Filters
              </Button>
            </div>

            <Table<TableMetadata>
              columns={columns}
              dataSource={metadataResponse?.items || []}
              loading={isLoading}
              pagination={{
                current: searchParams.page,
                pageSize: searchParams.size,
                total: metadataResponse?.total || 0,
                showSizeChanger: true,
                showQuickJumper: true,
                pageSizeOptions: ['10', '20', '50', '100'],
                showTotal: (total, range) =>
                  `${range[0]}-${range[1]} of ${total} metadata records`,
              }}
              onChange={handleTableChange}
              scroll={{ x: 1200 }}
              rowKey="id"
              locale={{
                emptyText: (
                  <Empty
                    image={Empty.PRESENTED_IMAGE_SIMPLE}
                    description="No metadata found"
                  >
                    <Button type="primary" icon={<PlusOutlined />}>
                      Generate Your First Metadata
                    </Button>
                  </Empty>
                ),
              }}
            />
          </Card>
        </Col>
      </Row>

      {/* Metadata Details Drawer */}
      <Drawer
        title={
          selectedMetadata && (
            <div>
              <Text strong>{selectedMetadata.table_name}</Text>
              <br />
              <Text type="secondary" style={{ fontSize: 12 }}>
                {selectedMetadata.database_name}.{selectedMetadata.schema_name}
              </Text>
            </div>
          )
        }
        placement="right"
        size="large"
        onClose={() => setDetailsVisible(false)}
        open={detailsVisible}
      >
        {selectedMetadata && (
          <div>
            <Descriptions
              bordered
              column={1}
              style={{ marginBottom: 24 }}
              items={[
                {
                  label: 'Table Name',
                  children: selectedMetadata.table_name,
                },
                {
                  label: 'Database',
                  children: `${selectedMetadata.database_name}.${selectedMetadata.schema_name}`,
                },
                {
                  label: 'Description',
                  children: selectedMetadata.description || 'No description available',
                },
                {
                  label: 'Business Context',
                  children: selectedMetadata.business_context || 'No business context available',
                },
                {
                  label: 'Data Quality Score',
                  children: selectedMetadata.data_quality_score ? (
                    <Progress
                      percent={selectedMetadata.data_quality_score}
                      strokeColor={getQualityColor(selectedMetadata.data_quality_score)}
                    />
                  ) : (
                    'Not available'
                  ),
                },
                {
                  label: 'Generation Type',
                  children: (
                    <Tag color={getGenerationTypeColor(selectedMetadata.generated_by)}>
                      {selectedMetadata.generated_by.toUpperCase()}
                    </Tag>
                  ),
                },
                {
                  label: 'Created',
                  children: dayjs(selectedMetadata.created_at).format('MMMM DD, YYYY [at] h:mm A'),
                },
                {
                  label: 'Last Updated',
                  children: dayjs(selectedMetadata.updated_at).format('MMMM DD, YYYY [at] h:mm A'),
                },
              ]}
            />

            <Title level={5}>Columns ({selectedMetadata.columns.length})</Title>
            <Table
              dataSource={selectedMetadata.columns}
              pagination={false}
              size="small"
              columns={[
                {
                  title: 'Name',
                  dataIndex: 'name',
                  key: 'name',
                  render: (name, record) => (
                    <div>
                      <Text strong>{name}</Text>
                      {record.primary_key && (
                        <Tag size="small" color="gold" style={{ marginLeft: 8 }}>
                          PK
                        </Tag>
                      )}
                    </div>
                  ),
                },
                {
                  title: 'Type',
                  dataIndex: 'type',
                  key: 'type',
                  render: (type) => <Tag>{type}</Tag>,
                },
                {
                  title: 'Description',
                  dataIndex: 'description',
                  key: 'description',
                  render: (description) => description || <Text type="secondary">No description</Text>,
                },
              ]}
              scroll={{ y: 300 }}
            />
          </div>
        )}
      </Drawer>

      {/* Advanced Filters Modal */}
      <Modal
        title="Advanced Filters"
        open={filterVisible}
        onCancel={() => setFilterVisible(false)}
        footer={null}
      >
        {/* TODO: Implement advanced filters */}
        <Text>Advanced filtering options coming soon...</Text>
      </Modal>
    </div>
  );
};

export default MetadataPage; 