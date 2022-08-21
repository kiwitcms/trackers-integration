RootSeeder.new.seed!

User.where(login: 'admin', force_password_change: true).update_all(force_password_change: false)

admin = User.find_by(login: 'admin')
hashed_value = Token::API.hash_function('26210315639327b10b56b7ef5d2f47f843c0ced3bafd1540fd4ecb30a06fa80f')
Token::API.create :user_id => admin.id, :value => hashed_value

Project.where(name: 'Demo project').update_all(public: false)
