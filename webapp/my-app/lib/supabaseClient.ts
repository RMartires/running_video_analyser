import { createClient } from '@supabase/supabase-js'

// TODO: Replace with your actual Supabase project URL and anon/public key
const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || '<YOUR_SUPABASE_URL>'
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || '<YOUR_SUPABASE_ANON_KEY>'

export const supabase = createClient(supabaseUrl, supabaseAnonKey) 