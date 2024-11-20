pub fn add_two_integers(a: i32, b: i32) -> i32 {
    a + b
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_add_two_integers() {
        assert_eq!(add_two_integers(1, 2), 3);
        assert_eq!(add_two_integers(-1, 1), 0);
        assert_eq!(add_two_integers(-5, -3), -8);
    }
}