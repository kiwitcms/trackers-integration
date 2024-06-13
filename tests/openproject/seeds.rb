# Copyright (c) 2022-2023 Alexander Todorov <atodorov@otb.bg>
#
# Licensed under GNU Affero General Public License v3 or later (AGPLv3+)
# https://www.gnu.org/licenses/agpl-3.0.html

Seeder.log_to_stdout!
RootSeeder.new.seed!

User.where(login: 'admin', force_password_change: true).update_all(force_password_change: false)

admin = User.find_by(login: 'admin')
hashed_value = Token::API.hash_function('26210315639327b10b56b7ef5d2f47f843c0ced3bafd1540fd4ecb30a06fa80f')
Token::API.create :user_id => admin.id, :value => hashed_value

bot = User.create!(
    :login => 'kiwitcms-bot',
    :firstname => 'Testing',
    :lastname => 'Bot',
    :mail => 'bot@example.com',
    :password => 'Hello-World',
)
hashed_value = Token::API.hash_function('c48c60020d8f61e612241889eff79e610410f1322811d8c20df25a71f3619e25')
Token::API.create :user_id => bot.id, :value => hashed_value

demo_project = Project.find_by(name: 'Demo project')
role = Role.find_by(name: 'Member')

m = bot.memberships.build(project: demo_project)
m.roles.append(role)
bot.memberships.append(m)

Project.where(name: 'Demo project').update_all(public: false)
