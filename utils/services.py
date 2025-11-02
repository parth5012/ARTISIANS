import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from bson.objectid import ObjectId
class UserService:
    """Service class to handle user operations"""

    @staticmethod
    def create_user(user_data,artisans,users):
        """Create a new user in appropriate collection"""
        user_type = user_data.get('user_type')

        # Hash the password
        user_data['password_hash'] = generate_password_hash(
            user_data['password'])
        del user_data['password']  # Remove plain password

        # Add timestamp
        user_data['created_at'] = datetime.utcnow()
        user_data['updated_at'] = datetime.utcnow()

        if user_type == 'artisan':
            # Additional artisan-specific fields
            artisan_data = {
                **user_data,
                'shop_name': None,
                'shop_description': None,
                'products_count': 0,
                'total_sales': 0,
                'rating': 0.0,
                'is_verified': False,
                'social_links': {},
                'shipping_info': {},
                'portfolio_images': []
            }
            result = artisans.insert_one(artisan_data)
            return result.inserted_id, 'artisan'
        else:
            # Regular user (buyer) specific fields
            buyer_data = {
                **user_data,
                'wishlist': [],
                'order_history': [],
                'shipping_addresses': [],
                'payment_methods': []
            }
            result = users.insert_one(buyer_data)
            return result.inserted_id, 'user'

    @staticmethod
    def find_user_by_email(email,artisans,users):
        """Find user in both collections by email"""
        # Check artisans first
        artisan = artisans.find_one({'email': email})
        if artisan:
            return artisan, 'artisan'

        # Check regular users
        user = users.find_one({'email': email})
        if user:
            return user, 'user'

        return None, None

    @staticmethod
    def get_user_by_id(user_id, user_type,artisans,users):
        """Get user by ID from appropriate collection"""
        if user_type == 'artisan':
            return artisans.find_one({'_id': ObjectId(user_id)})
        else:
            return users.find_one({'_id': ObjectId(user_id)})

    @staticmethod
    def update_user(user_id, user_type, update_data,artisans,users):
        """Update user in appropriate collection"""
        update_data['updated_at'] = datetime.utcnow()

        if user_type == 'artisan':
            return artisans.update_one(
                {'_id': ObjectId(user_id)},
                {'$set': update_data}
            )
        else:
            return users.update_one(
                {'_id': ObjectId(user_id)},
                {'$set': update_data}
            )


class ArtisanService:
    """Service class specifically for artisan operations"""

    @staticmethod
    def get_all_artisans(artisans,filters=None, limit=20, skip=0):
        """Get artisans with optional filters"""
        query = filters or {}
        return list(artisans.find(query).limit(limit).skip(skip))

    @staticmethod
    def get_artisan_by_craft(craft_type, artisans,limit=10):
        """Get artisans by craft type"""
        return list(artisans.find({'craft_type': craft_type}).limit(limit))

    @staticmethod
    def update_artisan_profile(artisans,artisan_id, profile_data):
        """Update artisan-specific profile data"""
        profile_data['updated_at'] = datetime.utcnow()
        return artisans.update_one(
            {'_id': ObjectId(artisan_id)},
            {'$set': profile_data}
        )

    @staticmethod
    def increment_product_count(artisans,artisan_id):
        """Increment product count for artisan"""
        return artisans.update_one(
            {'_id': ObjectId(artisan_id)},
            {'$inc': {'products_count': 1}}
        )
