
# CLEANUP GUIDE FOR OLD GUEST USERS
# ================================

# After consolidating data to MySelectedUser, you may want to clean up old guest users.

# 1. IDENTIFY GUEST USERS TO CLEAN
# Run this query to list guest users (excluding MySelectedUser):
db.users.find({
    "username": {"$regex": "^Guest_"},
    "username": {"$ne": "MySelectedUser"}
})

# 2. DELETE OLD GUEST USERS (BE CAREFUL!)
# This will delete all guest users except MySelectedUser:
# db.users.deleteMany({
#     "username": {"$regex": "^Guest_"},
#     "username": {"$ne": "MySelectedUser"}
# })

# 3. ARCHIVE INSTEAD OF DELETE (RECOMMENDED)
# First, create an archive collection:
# db.archive_users.insertMany(db.users.find({
#     "username": {"$regex": "^Guest_"},
#     "username": {"$ne": "MySelectedUser"}
# }))

# Then delete the original users:
# db.users.deleteMany({
#     "username": {"$regex": "^Guest_"},
#     "username": {"$ne": "MySelectedUser"}
# })

# 4. UPDATE AUTO-FIX SCRIPT
# Update auto-fix jobs.py to only work with MySelectedUser
# Remove random guest user creation and focus on MySelectedUser

# 5. FRONTEND CONFIGURATION
# Remove guest user creation from frontend
# Configure app to always use MySelectedUser
# Remove "Create Guest User" buttons/logic
