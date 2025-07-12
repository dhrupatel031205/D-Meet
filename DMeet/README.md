# DMeet - Location-Based Event Discovery Platform

**Tagline:** Where Every Local Event Becomes an Adventure!

DMeet is a full-featured, location-aware event discovery web application built with Django + GeoDjango. The platform allows users to discover local events, RSVP, create their own events, provide feedback, and make connections with other attendees.

## 🚀 Features

### 🌍 Core Functionality
- **Location-based Event Discovery**: Find events within 5, 10, 20, or 50km radius
- **Interactive Maps**: View events on Leaflet.js-powered maps with OpenStreetMap
- **Event Management**: Create, edit, and manage events with admin approval system
- **RSVP System**: Register for events with attendance limits
- **Real-time Filtering**: Filter by category, date, distance, and search terms

### 🤝 Social Features
- **Post-Event Connections**: Connect with up to 3 attendees per event after events end
- **Event Feedback**: Rate and review events (1-5 stars with comments)
- **User Profiles**: Set location, interests, and bio for personalized recommendations
- **Dashboard**: Comprehensive user dashboard with stats and quick actions

### 👤 User Management
- **Django Authentication**: Built-in user registration, login, and password management
- **Profile System**: Extended user profiles with location (PointField) and interests
- **Interest-based Recommendations**: Filter homepage events based on user preferences

### 🔧 Admin Features
- **Event Moderation**: Approve/reject user-submitted events
- **Category Management**: Manage event categories
- **Analytics**: View RSVP counts, feedback, and connection analytics
- **GeoDjango Admin**: OSM-powered geographic admin interface

## 🛠️ Tech Stack

- **Backend**: Django 5.1.7 + GeoDjango
- **Database**: PostgreSQL + PostGIS (with SQLite + SpatiaLite fallback)
- **Frontend**: Django Templates + Bootstrap 5 + Leaflet.js
- **Authentication**: Django built-in auth system
- **Forms**: Django forms + django-crispy-forms + crispy-bootstrap5
- **Maps**: Leaflet.js with OpenStreetMap tiles

## 📦 Installation & Setup

### Prerequisites
- Python 3.8+
- PostgreSQL + PostGIS (recommended) or SQLite + SpatiaLite
- GDAL/GEOS libraries for GeoDjango

### 1. Clone and Setup Environment
```bash
git clone <repository-url>
cd DMeet
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Database Configuration

#### Option A: PostgreSQL + PostGIS (Recommended)
```bash
# Install PostgreSQL and PostGIS
sudo apt-get install postgresql postgresql-contrib postgis

# Create database
sudo -u postgres createdb dmeet_db
sudo -u postgres psql dmeet_db -c "CREATE EXTENSION postgis;"

# Set environment variables
export DB_NAME=dmeet_db
export DB_USER=postgres
export DB_PASSWORD=your_password
export DB_HOST=localhost
export DB_PORT=5432
```

#### Option B: SQLite + SpatiaLite (Development)
```bash
export USE_SQLITE=1
```

### 3. Django Setup
```bash
cd DMeet
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
python manage.py collectstatic
```

### 4. Create Sample Data (Optional)
```bash
python manage.py shell
# In Django shell:
from core.models import EventCategory
EventCategory.objects.create(name="Music", description="Concerts, festivals, and musical events")
EventCategory.objects.create(name="Technology", description="Tech meetups, conferences, and workshops")
EventCategory.objects.create(name="Sports", description="Sports events, tournaments, and fitness activities")
EventCategory.objects.create(name="Food & Drink", description="Food festivals, tastings, and culinary events")
EventCategory.objects.create(name="Arts & Culture", description="Art exhibitions, theater, and cultural events")
```

### 5. Run Development Server
```bash
python manage.py runserver
```

Visit `http://127.0.0.1:8000` to access the application.

## 🔧 Configuration

### Environment Variables
- `DB_NAME`: PostgreSQL database name (default: dmeet_db)
- `DB_USER`: Database user (default: postgres)
- `DB_PASSWORD`: Database password
- `DB_HOST`: Database host (default: localhost)
- `DB_PORT`: Database port (default: 5432)
- `USE_SQLITE`: Set to use SQLite instead of PostgreSQL (development only)
- `GDAL_LIBRARY_PATH`: Path to GDAL library (if needed)
- `GEOS_LIBRARY_PATH`: Path to GEOS library (if needed)

### Production Settings
For production deployment, update the following in `settings.py`:
- Set `DEBUG = False`
- Configure `ALLOWED_HOSTS`
- Set up proper email backend for notifications
- Configure static files serving with WhiteNoise or CDN

## 📋 Usage

### For Users
1. **Register/Login**: Create an account or sign in
2. **Set Profile**: Add your location and interests for better recommendations
3. **Discover Events**: Browse events on homepage or map view
4. **RSVP**: Register for events you want to attend
5. **Attend Events**: Show up and enjoy!
6. **Give Feedback**: Rate and review events after they end
7. **Make Connections**: Connect with up to 3 people from each event

### For Event Organizers
1. **Create Events**: Use the event creation form with map location picker
2. **Wait for Approval**: Admin will review and approve your event
3. **Manage RSVPs**: View attendee list through admin interface
4. **Get Feedback**: Receive ratings and comments from attendees

### For Administrators
1. **Access Admin**: Visit `/admin/` to access Django admin
2. **Approve Events**: Review and approve submitted events
3. **Manage Categories**: Add/edit event categories
4. **Monitor Platform**: View user activity, RSVPs, and feedback

## 🗂️ Project Structure

```
DMeet/
├── DMeet/                  # Django project settings
│   ├── settings.py         # Main configuration
│   ├── urls.py            # URL routing
│   └── wsgi.py            # WSGI config
├── core/                   # Main application
│   ├── models.py          # Data models (Event, RSVP, Feedback, etc.)
│   ├── views.py           # View logic
│   ├── forms.py           # Django forms
│   ├── admin.py           # Admin interface
│   └── urls.py            # App URL patterns
├── templates/              # HTML templates
│   ├── base.html          # Base template with Bootstrap & Leaflet
│   ├── core/              # App-specific templates
│   └── registration/      # Auth templates
├── static/                 # Static files (CSS, JS, images)
├── requirements.txt        # Python dependencies
└── manage.py              # Django management script
```

## 🌟 Key Models

- **Event**: Main event model with GeoDjango PointField for location
- **EventCategory**: Categories for organizing events
- **Profile**: Extended user profile with location and interests
- **RSVP**: User registrations for events
- **Feedback**: Post-event ratings and comments (1-5 stars)
- **Connection**: Networking connections between attendees (max 3 per event)

## 🚀 Deployment

### Using Gunicorn + Nginx
```bash
pip install gunicorn
gunicorn DMeet.wsgi:application --bind 0.0.0.0:8000
```

### Using Docker (Optional)
Create a `Dockerfile` for containerized deployment:
```dockerfile
FROM python:3.9
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["gunicorn", "DMeet.wsgi:application", "--bind", "0.0.0.0:8000"]
```

## 🔒 Security Features

- CSRF protection on all forms
- User authentication for sensitive operations
- Event approval system to prevent spam
- Input validation and sanitization
- GeoDjango's built-in spatial query protections

## 🎨 Customization

### Styling
- Modify CSS variables in `base.html` for color scheme
- Bootstrap 5 classes for responsive design
- Custom CSS for event cards, maps, and components

### Maps
- Default map tiles use OpenStreetMap
- Easily configurable to use other tile providers
- Marker icons and popups customizable

### Categories
- Add new event categories through admin interface
- Category icons configurable via FontAwesome classes

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License. See LICENSE file for details.

## 🆘 Support

For issues and questions:
1. Check the Django documentation for GeoDjango setup
2. Ensure PostGIS is properly installed and configured
3. Verify GDAL/GEOS libraries are accessible
4. Check browser console for JavaScript errors

## 🎯 Future Enhancements

- [ ] REST API for mobile app development
- [ ] QR code check-in system
- [ ] Email/SMS notifications
- [ ] Social login (Google, Facebook)
- [ ] Event photos and galleries
- [ ] Payment integration for paid events
- [ ] Event recommendations using ML
- [ ] Real-time chat between connections

---

**DMeet** - Built with ❤️ using Django + GeoDjango