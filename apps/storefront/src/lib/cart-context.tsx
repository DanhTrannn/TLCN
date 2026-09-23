"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";

import {
  ApiError,
  getCart,
  removeCartItem,
  setCartItem,
  type Cart,
} from "./api";
import { useAuth } from "./auth";

interface CartContextValue {
  cart: Cart | null;
  loading: boolean;
  isOpen: boolean;
  openDrawer: () => void;
  closeDrawer: () => void;
  refreshCart: () => Promise<void>;
  updateItemQuantity: (variantPublicId: string, quantity: number) => Promise<void>;
  removeItem: (variantPublicId: string) => Promise<void>;
  addItemAndOpen: (variantPublicId: string, quantity?: number) => Promise<void>;
  itemCount: number;
}

const CartContext = createContext<CartContextValue | null>(null);

export function CartProvider({ children }: { children: ReactNode }) {
  const { customer, loading: authLoading } = useAuth();
  const [cart, setCart] = useState<Cart | null>(null);
  const [loading, setLoading] = useState(false);
  const [isOpen, setIsOpen] = useState(false);

  const refreshCart = useCallback(async () => {
    if (!customer) {
      setCart(null);
      return;
    }
    setLoading(true);
    try {
      const data = await getCart();
      setCart(data);
    } catch (err) {
      if (err instanceof ApiError && err.status === 401) {
        setCart(null);
      }
    } finally {
      setLoading(false);
    }
  }, [customer]);

  useEffect(() => {
    if (!authLoading) {
      void refreshCart();
    }
  }, [authLoading, refreshCart]);

  const openDrawer = useCallback(() => {
    setIsOpen(true);
  }, []);

  const closeDrawer = useCallback(() => {
    setIsOpen(false);
  }, []);

  const updateItemQuantity = useCallback(async (variantPublicId: string, quantity: number) => {
    if (quantity < 1) return;
    try {
      const updated = await setCartItem(variantPublicId, quantity);
      setCart(updated);
    } catch (err) {
      throw err;
    }
  }, []);

  const removeItem = useCallback(async (variantPublicId: string) => {
    try {
      const updated = await removeCartItem(variantPublicId);
      setCart(updated);
    } catch (err) {
      throw err;
    }
  }, []);

  const addItemAndOpen = useCallback(async (variantPublicId: string, quantity: number = 1) => {
    try {
      const updated = await setCartItem(variantPublicId, quantity);
      setCart(updated);
      setIsOpen(true);
    } catch (err) {
      throw err;
    }
  }, []);

  const itemCount = useMemo(() => {
    if (!cart?.items) return 0;
    return cart.items.reduce((total, item) => total + item.quantity, 0);
  }, [cart]);

  const value = useMemo<CartContextValue>(
    () => ({
      cart,
      loading,
      isOpen,
      openDrawer,
      closeDrawer,
      refreshCart,
      updateItemQuantity,
      removeItem,
      addItemAndOpen,
      itemCount,
    }),
    [
      cart,
      loading,
      isOpen,
      openDrawer,
      closeDrawer,
      refreshCart,
      updateItemQuantity,
      removeItem,
      addItemAndOpen,
      itemCount,
    ]
  );

  return <CartContext.Provider value={value}>{children}</CartContext.Provider>;
}

export function useCartDrawer(): CartContextValue {
  const ctx = useContext(CartContext);
  if (!ctx) {
    throw new Error("useCartDrawer must be used within CartProvider");
  }
  return ctx;
}
