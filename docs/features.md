# Screenshots

This page showcases the Django Redis Panel interface with detailed screenshots of all major features.

## Django Admin Integration

Django Redis Panel integrates seamlessly into your existing Django admin interface. A new section for Redis management appears alongside your regular Django models.

!!! note "No Models Required"
    This application doesn't introduce any Django models or require database migrations. It's purely a Redis management interface.

![Admin Home](https://raw.githubusercontent.com/yassi/dj-redis-panel/main/images/admin_home.png)

**Features shown:**
- Clean integration with Django admin styling
- Redis Panel section in the admin home
- "Manage Redis keys and values" entry point

## Instance List

The main landing page shows all configured Redis instances with their connection status and basic information.

![Instance List](https://raw.githubusercontent.com/yassi/dj-redis-panel/main/images/instances_list.png)

**Features shown:**
- Multiple Redis instance support
- Connection status indicators
- Instance descriptions and connection details
- Quick access to instance management

## Instance Overview

Each Redis instance has a detailed overview page showing server information, database statistics, and quick navigation options.

![Instance Overview](https://raw.githubusercontent.com/yassi/dj-redis-panel/main/images/instance_overview.png)

**Features shown:**
- Server information (version, uptime, memory usage)
- Database statistics with key counts
- Memory usage per database
- Quick links to browse keys in specific databases
- Real-time connection status

## Key Search - Page-Based Pagination

The key search interface supports traditional page-based navigation, perfect for smaller datasets and when you need predictable page jumping.

![Key Search - Page Index](https://raw.githubusercontent.com/yassi/dj-redis-panel/main/images/key_search_page_index.png)

**Features shown:**
- Search pattern input with examples
- Database selection dropdown
- Traditional pagination with page numbers
- Key type indicators
- Results per page selection
- Total key count display

## Key Search - Cursor-Based Pagination

For larger datasets, cursor-based pagination provides better performance and stability during data changes.

![Key Search - Cursor](https://raw.githubusercontent.com/yassi/dj-redis-panel/main/images/key_search_cursor.png)

**Features shown:**
- Efficient cursor-based navigation
- Next/Previous controls
- Stable pagination during key modifications
- Better performance with large key sets
- Same search and filtering capabilities

## Key Detail - String Values

String keys are displayed with syntax highlighting and full editing capabilities.

![Key Detail - String](https://raw.githubusercontent.com/yassi/dj-redis-panel/main/images/key_detail_string.png)

**Features shown:**
- Key information panel (name, type, TTL, size)
- Formatted value display with syntax highlighting
- Edit functionality with large text area
- TTL management controls
- Delete confirmation
- JSON/XML automatic formatting

## Key Detail - Complex Data Structures

Complex Redis data types like hashes are displayed in an organized, tabular format for easy browsing.

![Key Detail - Hash](https://raw.githubusercontent.com/yassi/dj-redis-panel/main/images/key_detail_hash.png)

**Features shown:**
- Hash fields displayed in a clean table format
- Field names and values clearly separated
- Pagination for large hashes
- Key metadata (type, field count, memory usage)
- Consistent interface design

## Interface Highlights

### Design Consistency

All interfaces maintain consistency with Django's admin theme:

- **Color Scheme**: Matches Django admin colors and styling
- **Typography**: Uses Django's font stack and sizing
- **Navigation**: Familiar breadcrumb and navigation patterns
- **Forms**: Standard Django form styling and validation

### Dark Mode Support

Django Redis Panel automatically adapts to Django admin's dark mode:

- **Automatic Detection**: Follows Django admin theme preferences
- **Consistent Theming**: All components support both light and dark modes
- **Accessibility**: Maintains proper contrast ratios in both modes

### Responsive Design

The interface works well across different screen sizes:

- **Mobile Friendly**: Touch-friendly interface elements
- **Tablet Optimized**: Efficient use of screen space
- **Desktop Enhanced**: Full feature set on larger screens

### User Experience Features

#### Visual Feedback

- **Loading States**: Clear indicators during operations
- **Success Messages**: Confirmation of successful actions
- **Error Handling**: Clear error messages with helpful suggestions

#### Navigation Aids

- **Breadcrumbs**: Always know where you are
- **Quick Links**: Fast navigation between related pages
- **Search History**: Remember recent search patterns

#### Data Presentation

- **Syntax Highlighting**: JSON, XML, and other formats are highlighted
- **Data Formatting**: Automatic formatting for better readability
- **Truncation**: Long values are intelligently truncated with expand options

## Accessibility Features

### Screen Reader Support

- **Semantic HTML**: Proper heading structure and landmarks
- **Alt Text**: Descriptive text for all images and icons
- **ARIA Labels**: Enhanced accessibility for interactive elements

### Keyboard Navigation

- **Tab Order**: Logical tab sequence through all interface elements
- **Keyboard Shortcuts**: Quick access to common functions
- **Focus Indicators**: Clear visual focus indicators

### Color and Contrast

- **High Contrast**: Meets WCAG AA standards
- **Color Independence**: Information not conveyed by color alone
- **Customizable**: Respects system accessibility preferences

## Browser Compatibility

Django Redis Panel works across all modern browsers:

- **Chrome/Chromium**: Full feature support
- **Firefox**: Complete compatibility
- **Safari**: Native macOS/iOS experience
- **Edge**: Modern Edge (Chromium-based) support

## Mobile Experience

While primarily designed for desktop use, the interface is mobile-friendly:

- **Touch Targets**: Appropriately sized for touch interaction
- **Scrolling**: Smooth scrolling and navigation
- **Viewport**: Proper mobile viewport configuration
- **Performance**: Optimized for mobile network conditions

## Performance Considerations

The interface is optimized for performance:

- **Lazy Loading**: Key values loaded on demand
- **Efficient Pagination**: Minimal server round trips
- **Caching**: Appropriate caching of static resources
- **Compression**: Optimized asset delivery

## Customization Options

While maintaining Django admin consistency, some customization is possible:

- **CSS Overrides**: Custom styling through Django's static files
- **Template Extensions**: Extend templates for additional functionality
- **Theme Integration**: Works with Django admin theme packages

## Getting the Most from the Interface

### Pro Tips

1. **Use Specific Patterns**: Instead of `*`, use patterns like `user:*` for better performance
2. **Database Selection**: Use the database dropdown to narrow your search scope
3. **Cursor Pagination**: Enable for large datasets in your configuration
4. **Keyboard Shortcuts**: Learn the tab navigation for faster operation

### Best Practices

1. **Test in Development**: Always test destructive operations in a safe environment
2. **Use Read-Only Mode**: Configure read-only access for production viewing
3. **Monitor Performance**: Watch Redis performance when browsing large datasets
4. **Regular Backups**: Ensure proper Redis backup procedures before making changes

The screenshots above represent the current version of Django Redis Panel. The interface continues to evolve with new features and improvements in each release.
