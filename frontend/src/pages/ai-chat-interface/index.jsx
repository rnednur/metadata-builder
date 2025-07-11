import React, { useState, useRef, useEffect } from 'react';
import { useLocation, useSearchParams } from 'react-router-dom';
import Header from '../../components/ui/Header';
import Sidebar from '../../components/ui/Sidebar';
import Breadcrumb from '../../components/ui/Breadcrumb';
import ChatHeader from './components/ChatHeader';
import ChatMessage from './components/ChatMessage';
import MessageInput from './components/MessageInput';
import ContextSidebar from './components/ContextSidebar';
import SchemaAttachmentModal from './components/SchemaAttachmentModal';
import { agentAPI, apiUtils } from '../../services/api';

const AIChatInterface = () => {
  const location = useLocation();
  const [searchParams] = useSearchParams();
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
  const [isContextOpen, setIsContextOpen] = useState(false);
  const [isSchemaModalOpen, setIsSchemaModalOpen] = useState(false);
  const [messages, setMessages] = useState([]);
  const [isTyping, setIsTyping] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  // Extract context from URL parameters or location state
  const getCurrentContext = () => {
    // Try to get context from URL parameters
    const database = searchParams.get('database') || searchParams.get('db');
    const schema = searchParams.get('schema');
    const table = searchParams.get('table');
    const dbType = searchParams.get('type');
    
    // Try to get context from location state (when navigated from another page)
    const state = location.state;
    
    // Try to parse context from current URL pathname if it follows common patterns
    // e.g., /schema-explorer/bq_public/samples/github_nested
    // or similar patterns where table info is in the URL
    const pathParts = location.pathname.split('/');
    let pathDatabase, pathSchema, pathTable;
    
    // Look for common patterns in the URL
    if (pathParts.includes('schema-explorer') && pathParts.length >= 5) {
      const schemaIndex = pathParts.indexOf('schema-explorer');
      pathDatabase = pathParts[schemaIndex + 1];
      pathSchema = pathParts[schemaIndex + 2];
      pathTable = pathParts[schemaIndex + 3];
    }
    
    // Also check if localStorage has recent table context (as a fallback)
    let storageContext = {};
    try {
      const recentContext = localStorage.getItem('recent_table_context');
      if (recentContext) {
        storageContext = JSON.parse(recentContext);
      }
    } catch (e) {
      console.warn('Could not parse recent table context from localStorage');
    }
    
    const context = {
      database: database || state?.database || state?.connectionName || pathDatabase || storageContext.database,
      schema: schema || state?.schema || state?.schemaName || pathSchema || storageContext.schema,
      table: table || state?.table || state?.tableName || pathTable || storageContext.table,
      databaseType: dbType || state?.databaseType || state?.type || storageContext.databaseType,
      tableMetadata: state?.tableMetadata || storageContext.tableMetadata
    };
    
    // If we found a good context, save it to localStorage for future use
    if (context.table && context.database) {
      try {
        localStorage.setItem('recent_table_context', JSON.stringify(context));
      } catch (e) {
        console.warn('Could not save table context to localStorage');
      }
    }
    
    return context;
  };

  const toggleSidebarCollapse = () => {
    setIsSidebarCollapsed(!isSidebarCollapsed);
  };
  const messagesEndRef = useRef(null);

  // Generate initial message based on context
  const getInitialMessage = () => {
    const context = getCurrentContext();
    let content = "Hello! I'm your AI assistant for database metadata analysis. I can help you understand your database schema, relationships, and provide insights about your data structures.";
    
    if (context.table) {
      content += `\n\nI can see you're currently analyzing the **${context.table}** table`;
      if (context.schema) {
        content += ` in the **${context.schema}** schema`;
      }
      if (context.database) {
        content += ` from the **${context.database}** database`;
      }
      content += ". I can help you with:\n";
      content += "• Analyzing missing metadata fields like domain and category\n";
      content += "• Generating better descriptions for tables and columns\n";
      content += "• Understanding data relationships and patterns\n";
      content += "• Improving data quality and documentation\n\n";
      content += "What would you like to know about this table?";
    } else {
      content += "\n\nWhat would you like to know about your databases?";
    }
    
    return [{
      id: 1,
      content,
      isUser: false,
      timestamp: new Date(Date.now() - 300000),
      status: 'delivered'
    }];
  };

  useEffect(() => {
    setMessages(getInitialMessage());
  }, [location, searchParams]);

  useEffect(() => {
    scrollToBottom();
  }, [messages, isTyping]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  // Extract mentioned objects from user message
  const extractMentionedObjects = (content) => {
    const mentionPattern = /@(\w+)/g;
    const mentions = [];
    let match;
    
    while ((match = mentionPattern.exec(content)) !== null) {
      mentions.push(match[1]);
    }
    
    return mentions;
  };

  // Handle metadata correction requests
  const handleMetadataCorrection = async (content, extractedObjects) => {
    // Simulate metadata correction processing
    const delay = (ms) => new Promise(resolve => setTimeout(resolve, ms));
    
    // Simulate processing time
    await delay(1000);
    
    const actions = [];
    const suggestions = [];
    
    // Determine the type of correction needed
    if (content.toLowerCase().includes('fix') || content.toLowerCase().includes('correct')) {
      actions.push('metadata_correction');
      
      if (extractedObjects.length > 0) {
        actions.push('query_execution');
        suggestions.push('I can help you run queries to get additional context for these objects.');
      }
    }
    
    if (content.toLowerCase().includes('categorical') || content.toLowerCase().includes('values')) {
      actions.push('categorical_analysis');
      suggestions.push('Would you like me to analyze categorical values for better metadata?');
    }
    
    let responseContent = `I understand you want to work with metadata correction`;
    
    if (extractedObjects.length > 0) {
      responseContent += ` for: ${extractedObjects.map(obj => `@${obj}`).join(', ')}.`;
      
      responseContent += `\n\nHere's what I can do:`;
      responseContent += `\n• Analyze current metadata for these objects`;
      responseContent += `\n• Run queries to get additional context`;
      responseContent += `\n• Suggest improvements to descriptions`;
      responseContent += `\n• Update categorical values`;
      responseContent += `\n• Fix data type classifications`;
      
      // Add specific actions for each object
      extractedObjects.forEach(obj => {
        responseContent += `\n\n**For @${obj}:**`;
        responseContent += `\n• \`SELECT * FROM ${obj} LIMIT 10\` - Sample data`;
        responseContent += `\n• \`SELECT DISTINCT column_name FROM ${obj} WHERE column_name IS NOT NULL\` - Get unique values`;
        responseContent += `\n• Analyze column patterns and suggest better descriptions`;
      });
      
      responseContent += `\n\nWould you like me to start with any of these actions?`;
    } else {
      responseContent += `. I can help you:`;
      responseContent += `\n• Fix table descriptions`;
      responseContent += `\n• Update column metadata`;
      responseContent += `\n• Analyze categorical values`;
      responseContent += `\n• Run queries for additional context`;
      responseContent += `\n\nPlease specify which table or column you'd like to work with using @ mentions.`;
    }
    
    return {
      response: responseContent,
      intent: 'metadata_correction',
      entities: extractedObjects,
      actions_taken: actions,
      suggestions: suggestions
    };
  };

  // Execute query for additional context
  const executeQuery = async (query, objectName) => {
    // This would integrate with your database API
    try {
      // Mock query execution
      return {
        success: true,
        data: [
          { column: 'sample_column', value: 'sample_value' },
          { column: 'another_column', value: 'another_value' }
        ],
        message: `Query executed successfully for ${objectName}`
      };
    } catch (error) {
      return {
        success: false,
        error: error.message,
        message: `Failed to execute query for ${objectName}`
      };
    }
  };

  const breadcrumbItems = [
    { label: 'Dashboard', path: '/database-connections-dashboard' },
    { label: 'AI Chat Interface' }
  ];

  const handleSendMessage = async (content) => {
    if (!content.trim()) return;

    const userMessage = {
      id: Date.now(),
      content,
      isUser: true,
      timestamp: new Date(),
      status: 'sending'
    };

    setMessages(prev => [...prev, userMessage]);
    setIsLoading(true);
    setIsTyping(true);

    try {
      // Update message status to sent
      setMessages(prev => 
        prev.map(msg => 
          msg.id === userMessage.id 
            ? { ...msg, status: 'sent' }
            : msg
        )
      );

      // Check if this is a metadata correction request
      const isMetadataCorrection = content.includes('@') || 
                                 content.toLowerCase().includes('fix metadata') ||
                                 content.toLowerCase().includes('correct metadata') ||
                                 content.toLowerCase().includes('update metadata');

      let response;
      let aiResponseData;

      if (isMetadataCorrection) {
        // Handle metadata correction request
        const extractedObjects = extractMentionedObjects(content);
        aiResponseData = await handleMetadataCorrection(content, extractedObjects);
      } else {
        // Send message to AI agent
        const userId = 'user_' + Date.now(); // In a real app, this would come from authentication
        const currentContext = getCurrentContext();
        const chatRequest = apiUtils.buildChatRequest(userId, content, null, currentContext);
        
        response = await agentAPI.chat(chatRequest);
        aiResponseData = response.data;
      }
      
      setIsTyping(false);
      
      const responseMessage = {
        id: Date.now() + 1,
        content: aiResponseData.response,
        isUser: false,
        timestamp: new Date(),
        status: 'delivered',
        intent: aiResponseData.intent,
        entities: aiResponseData.entities,
        actions: aiResponseData.actions_taken,
        suggestions: aiResponseData.suggestions
      };

      setMessages(prev => [...prev, responseMessage]);

      // Update user message to delivered
      setMessages(prev => 
        prev.map(msg => 
          msg.id === userMessage.id 
            ? { ...msg, status: 'delivered' }
            : msg
        )
      );

    } catch (error) {
      setIsTyping(false);
      
      console.error('Failed to send message:', error);
      
      // Show error message
      const errorMessage = {
        id: Date.now() + 1,
        content: `Sorry, I encountered an error: ${apiUtils.handleApiError(error)}. Please try again.`,
        isUser: false,
        timestamp: new Date(),
        status: 'delivered',
        isError: true
      };

      setMessages(prev => [...prev, errorMessage]);

      // Update user message to failed
      setMessages(prev => 
        prev.map(msg => 
          msg.id === userMessage.id 
            ? { ...msg, status: 'failed' }
            : msg
        )
      );
    } finally {
      setIsLoading(false);
    }
  };

  const generateAIResponse = (userInput) => {
    const input = userInput.toLowerCase();
    
    if (input.includes('users') && input.includes('orders')) {
      return `Based on your database schema, I can see a clear relationship between the users and orders tables:\n\n**Relationship Analysis:**\n- The orders table has a foreign key 'user_id' that references the users table's 'id' column\n- This creates a one-to-many relationship (one user can have multiple orders)\n\n**Key Insights:**\n- Users table contains 50,000 records with 12 columns including email, created_at, and last_login\n- Orders table has 125,000 records with 8 columns including user_id, total_amount, and status\n- Average orders per user: ~2.5 orders\n\n\`\`\`sql\nSELECT \n  u.email,\n  COUNT(o.id) as order_count,\n  SUM(o.total_amount) as total_spent\nFROM users u\nLEFT JOIN orders o ON u.id = o.user_id\nGROUP BY u.id, u.email\nORDER BY total_spent DESC;\n\`\`\`\n\nWould you like me to analyze any specific aspects of this relationship or explore other table connections?`;
    }
    
    if (input.includes('products') || input.includes('inventory')) {
      return `The products table is a central entity in your e-commerce schema:\n\n**Table Overview:**\n- 2,500 product records with 15 columns\n- Key columns include: id, name, description, price, category_id, stock_quantity\n- Connected to order_items table via product_id foreign key\n\n**Data Quality Insights:**\n- 98% of products have valid descriptions\n- 15 products currently have zero stock\n- Average price: $45.67\n- Most popular category: Electronics (35% of products)\n\n\`\`\`sql\nSELECT \n  category_id,\n  COUNT(*) as product_count,\n  AVG(price) as avg_price,\n  SUM(CASE WHEN stock_quantity = 0 THEN 1 ELSE 0 END) as out_of_stock\nFROM products\nGROUP BY category_id;\n\`\`\`\n\nWould you like me to dive deeper into product performance or inventory analysis?`;
    }
    
    if (input.includes('schema') || input.includes('structure')) {
      return `Here's an overview of your database schema structure:\n\n**Database: ecommerce_prod**\n- Schema: public\n- Tables: 4 main tables with clear relationships\n\n**Table Hierarchy:**\n1. **users** (50K records) - Customer information\n2. **products** (2.5K records) - Product catalog\n3. **orders** (125K records) - Order transactions\n4. **order_items** (300K records) - Order line items\n\n**Key Relationships:**\n- users → orders (1:many)\n- orders → order_items (1:many)\n- products → order_items (1:many)\n\n**Analytics Database: analytics_db**\n- Schema: reporting\n- Tables: customer_metrics, sales_summary\n- Purpose: Aggregated data for business intelligence\n\nThe schema follows good normalization practices with proper foreign key constraints. Would you like me to explain any specific table or relationship in more detail?`;
    }
    
    if (input.includes('performance') || input.includes('optimization')) {
      return `Based on the table sizes and query patterns, here are some performance insights:\n\n**Table Performance Analysis:**\n\n**High Volume Tables:**\n- order_items (300K records) - Consider partitioning by date\n- orders (125K records) - Index on user_id and created_at recommended\n\n**Optimization Recommendations:**\n1. **Indexing Strategy:**\n   - Add composite index on orders(user_id, created_at)\n   - Consider index on products(category_id, price)\n   - Review order_items(order_id, product_id) index usage\n\n2. **Query Optimization:**\n   - Use LIMIT clauses for large result sets\n   - Consider materialized views for complex aggregations\n   - Implement proper pagination for order history\n\n\`\`\`sql\n-- Suggested indexes\nCREATE INDEX idx_orders_user_date ON orders(user_id, created_at);\nCREATE INDEX idx_products_category_price ON products(category_id, price);\nCREATE INDEX idx_order_items_order_product ON order_items(order_id, product_id);\n\`\`\`\n\nWould you like me to analyze specific query patterns or suggest additional optimizations?`;
    }
    
    // Default response
    return `I understand you're asking about "${userInput}". Let me help you with that.\n\nBased on your current database connections, I can provide insights about:\n\n• **Schema exploration** - Table structures and relationships\n• **Data analysis** - Column types, constraints, and patterns\n• **Performance insights** - Query optimization suggestions\n• **Metadata generation** - Automated documentation\n• **Business intelligence** - LookML model recommendations\n\nCould you be more specific about what aspect you'd like me to focus on? For example:\n- "Explain the relationship between users and orders tables"\n- "What are the key columns in the products table?"\n- "Show me tables with foreign key relationships"\n- "Analyze data quality in the customer_analytics schema"`;
  };

  const handleAttachSchema = () => {
    setIsSchemaModalOpen(true);
  };

  const handleSchemaAttachment = (selectedItems) => {
    const attachmentMessage = {
      id: Date.now(),
      content: `I've attached ${selectedItems.length} schema object${selectedItems.length !== 1 ? 's' : ''} to our conversation:\n\n${selectedItems.map(item => `• ${item.name || item.fullPath}`).join('\n')}\n\nHow can I help you analyze these objects?`,
      isUser: false,
      timestamp: new Date(),
      status: 'delivered'
    };
    
    setMessages(prev => [...prev, attachmentMessage]);
  };

  const handleExportChat = () => {
    // Export functionality handled in ChatHeader component
    console.log('Chat exported');
  };

  const handleClearChat = () => {
    setMessages(getInitialMessage());
  };

  return (
    <div className="min-h-screen bg-background">
      <Header 
        onMenuToggle={() => setIsSidebarOpen(!isSidebarOpen)}
        isMenuOpen={isSidebarOpen}
        isSidebarCollapsed={isSidebarCollapsed}
      />
      
      <Sidebar 
        isOpen={isSidebarOpen}
        onClose={() => setIsSidebarOpen(false)}
        isCollapsed={isSidebarCollapsed}
        onToggleCollapse={toggleSidebarCollapse}
      />

      <main className={`pt-16 ${isSidebarCollapsed ? 'lg:pl-16' : 'lg:pl-60'}`}>
        <div className="flex h-[calc(100vh-4rem)]">
          {/* Chat Area */}
          <div className="flex-1 flex flex-col lg:mr-80">
            {/* Breadcrumb */}
            <div className="p-4 border-b border-border bg-surface">
              <Breadcrumb items={breadcrumbItems} />
            </div>

            {/* Chat Header */}
            <ChatHeader
              onToggleContext={() => setIsContextOpen(!isContextOpen)}
              onExportChat={handleExportChat}
              onClearChat={handleClearChat}
              messageCount={messages.length - 1} // Exclude initial message from count
            />

            {/* Messages Area */}
            <div className="flex-1 overflow-y-auto p-4 bg-surface">
              <div className="max-w-4xl mx-auto">
                {messages.map((message) => (
                  <ChatMessage
                    key={message.id}
                    message={message}
                    isUser={message.isUser}
                    timestamp={message.timestamp}
                    intent={message.intent}
                    entities={message.entities}
                    actions={message.actions}
                    suggestions={message.suggestions}
                  />
                ))}
                
                {isTyping && (
                  <ChatMessage
                    message={{ content: '' }}
                    isUser={false}
                    timestamp={new Date()}
                    isTyping={true}
                  />
                )}
                
                <div ref={messagesEndRef} />
              </div>
            </div>

            {/* Message Input */}
            <MessageInput
              onSendMessage={handleSendMessage}
              onAttachSchema={handleAttachSchema}
              isLoading={isLoading}
            />
          </div>

          {/* Context Sidebar */}
          <ContextSidebar
            isOpen={isContextOpen}
            onClose={() => setIsContextOpen(false)}
          />
        </div>
      </main>

      {/* Schema Attachment Modal */}
      <SchemaAttachmentModal
        isOpen={isSchemaModalOpen}
        onClose={() => setIsSchemaModalOpen(false)}
        onAttach={handleSchemaAttachment}
      />
    </div>
  );
};

export default AIChatInterface;